import argparse
import json
import csv

def load_json_data(json_file_path):
    """Loads data from a JSON file."""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        return None

def prepare_publisher_lookup(publishers_data):
    """Creates a lookup table for publishers by name."""
    publisher_lookup = {}
    if publishers_data:
        for publisher in publishers_data:
            key = (publisher.get('firstname', '').lower(), publisher.get('lastname', '').lower())
            publisher_lookup[key] = publisher.get('id')
    return publisher_lookup

def prepare_reports_lookup(reports_data):
    """Creates a lookup table for reports by user_id, year, and month."""
    reports_lookup = {}
    if reports_data:
        for report in reports_data:
            # Ensure year and month are integers if they exist
            year = report.get('year')
            month = report.get('month')
            user_id = report.get('user_id')
            if user_id is not None and year is not None and month is not None:
                try:
                    key = (user_id, int(year), int(month))
                    reports_lookup[key] = report
                except ValueError:
                    print(f"Warning: Could not parse year/month as integers for report with user_id {user_id}")
    return reports_lookup

# Helper function to determine publisher role
def get_publisher_role(report):
    """Determines the publisher's role based on the report."""
    if not report or report.get('pioneer') is None:
        return "Non-Pioneer"
    pioneer_status = str(report.get('pioneer', '')).lower() # Ensure it's a string and lowercased 
    if "auxiliary" in pioneer_status:
        return "Auxiliary Pioneer"
    elif "regular" in pioneer_status:
        return "Regular Pioneer"
    elif "special" in pioneer_status:
        return "Special Pioneer"
    return "Non-Pioneer"

def process_csv_file(csv_file_path, target_month_str, publisher_lookup, reports_lookup):
    """Processes the CSV file, matching rows with JSON data for the target month."""
    updated_rows = []
    fieldnames = []
    try:
        target_year, target_month = map(int, target_month_str.split('-'))
    except ValueError:
        print(f"Error: Invalid month format '{target_month_str}'. Please use YYYY-MM.")
        return updated_rows, fieldnames # Return empty list and no fieldnames
    try:
        with open(csv_file_path, 'r', newline='') as f_csv:
            reader = csv.DictReader(f_csv)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            if not fieldnames:
                print(f"Warning: Could not read fieldnames from CSV: {csv_file_path}. Cannot proceed with writing.")
                return updated_rows, fieldnames

            for row in reader:
                # Ensure 'Date', 'FirstName', 'LastName' exist in the row
                csv_month_str = row.get('Date')
                first_name = row.get('FirstName')
                last_name = row.get('LastName')

                if not all([csv_month_str, first_name, last_name]):
                    print(f"Warning: Skipping row due to missing required fields (Date, FirstName, or LastName): {row}")
                    updated_rows.append(row) # Keep the row as is
                    continue

                if csv_month_str == target_month_str:
                    publisher_key = (first_name.lower(), last_name.lower())
                    publisher_id = publisher_lookup.get(publisher_key)

                    if publisher_id is not None:
                        report_key = (publisher_id, target_year, target_month)
                        report = reports_lookup.get(report_key)

                        if report:
                            print(f"Found report for {first_name} {last_name} for month {target_month_str}. Updating row.")
                            row['SharedInMinistry'] = 'True'
                            row['BibleStudies'] = str(report.get('studies', 0) or 0)
                            publisher_role = get_publisher_role(report)
                            row['AP'] = 'True' if publisher_role == "Auxiliary Pioneer" else 'False'
                            hours = 0
                            if publisher_role != "Non-Pioneer":
                                minutes = report.get('minutes', 0) or 0
                                hours = minutes // 60 # Integer division for whole hours
                            row['Hours'] = str(hours)
                            credit_hours = report.get('credithours', 0) or 0
                            row['Credit'] = str(credit_hours)
                            row['Remarks'] = str(report.get('remarks', '') or '')
                        else:
                            print(f"No report found for {first_name} {last_name} (ID: {publisher_id}) for month {target_month_str}. Setting defaults.")
                            row['SharedInMinistry'] = 'False'
                            row['BibleStudies'] = '0'
                            row['AP'] = 'False'
                            row['Hours'] = '0'
                            row['Credit'] = '0'
                            row['Remarks'] = ''
                    else:
                        # This case handles when the publisher in the CSV (for the target month) is not in the JSON publisher list at all.
                        print(f"Publisher {first_name} {last_name} not found in JSON data (publisher lookup). Setting defaults for month {target_month_str}.")
                        row['SharedInMinistry'] = 'False'
                        row['BibleStudies'] = '0'
                        row['AP'] = 'False'
                        row['Hours'] = '0'
                        row['Credit'] = '0'
                        row['Remarks'] = ''
                # Add the row (either original, or modified if it was the target month) to the list of updated_rows.
                updated_rows.append(row)
        print(f"\nFinished processing CSV file: {csv_file_path}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred while processing the CSV file: {e}")
    return updated_rows, fieldnames

def write_updated_csv(csv_file_path, data_rows, fieldnames):
    """Writes the updated data rows back to the CSV file."""
    if not fieldnames:
        print("Error: No fieldnames provided. Cannot write CSV.")
        return False
    if not data_rows:
        print("Info: No data rows to write.") # This might not be an error, could be an empty processed list.
        # It might be desirable to still write an empty file with headers, or handle as per requirements.
        # For now, we'll proceed to write, which would create an empty file with headers if data_rows is empty.
        # Consider if an empty data_rows should prevent writing or not.
    try:
        with open(csv_file_path, 'w', newline='') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"Successfully wrote updated data to {csv_file_path}")
        return True
    except IOError:
        print(f"Error: Could not write to CSV file at {csv_file_path}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while writing the CSV file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Update CSV file with data from JSON file for a specific month.")
    parser.add_argument("--csv-file", required=True, help="The path to the target CSV file.")
    parser.add_argument("--json-file", required=True, help="The path to the source JSON file.")
    parser.add_argument("--month", required=True, help="The target month in YYYY-MM format.")

    args = parser.parse_args()

    print(f"CSV File: {args.csv_file}")
    print(f"JSON File: {args.json_file}")
    print(f"Month: {args.month}")

    json_data = load_json_data(args.json_file)

    if json_data:
        publisher_lookup = prepare_publisher_lookup(json_data.get('publishers'))
        reports_lookup = prepare_reports_lookup(json_data.get('reports'))

        print(f"\nPublisher Lookup Size: {len(publisher_lookup)}")
        if publisher_lookup and len(publisher_lookup) > 0 :
            print("Sample Publisher Lookup Entries (first 3):")
            for i, (key, value) in enumerate(publisher_lookup.items()):
                print(f"  {key}: {value}")
                if i >= 2:
                    break
        print(f"\nReports Lookup Size: {len(reports_lookup)}")
        if reports_lookup and len(reports_lookup) > 0:
            print("Sample Reports Lookup Entries (first 3):")
            for i, (key, value) in enumerate(reports_lookup.items()):
                # Print relevant parts of the report for verification
                print(f"  {key}: Pioneer status - {value.get('pioneer', 'N/A')}, Minutes - {value.get('minutes', 'N/A')}, Studies - {value.get('studies', 'N/A')}")
                if i >= 2:
                    break

        print("\nProcessing CSV file...")
        # Ensure that the CSV file is expected to have columns like:
        # FirstName, LastName, Date, SharedInMinistry, BibleStudies, AP, Hours, Credit, Remarks
        # The script will add/update these based on JSON data or set defaults.
        processed_rows, fieldnames = process_csv_file(args.csv_file, args.month, publisher_lookup, reports_lookup)
        if not fieldnames:
            # This typically means process_csv_file exited early due to a critical error (e.g., invalid month format, CSV not found, or unreadable headers)
            print("\nCritical error during CSV processing or CSV headers unreadable. Output file not written.")
        elif not processed_rows:
            # Fieldnames were read, but no data rows were processed or returned.
            # This could be an empty CSV or all rows were skipped.
            print(f"\nCSV processing returned no data rows (Headers found: {', '.join(fieldnames)}).")
            # Decide if writing an empty file (headers only) is the correct action.
            # For this script, we will write the headers to reflect that the file was processed.
            if write_updated_csv(args.csv_file, [], fieldnames):
                print(f"CSV file '{args.csv_file}' written with headers only as no data rows were processed/returned.")
            else:
                print(f"Failed to write CSV file '{args.csv_file}' with headers only.")
        else:
            # Both fieldnames and processed_rows are available and processed_rows is not empty.
            print(f"\nCSV processing complete. {len(processed_rows)} rows processed and updated (in memory).")
            if write_updated_csv(args.csv_file, processed_rows, fieldnames):
                print(f"CSV file '{args.csv_file}' updated successfully.")
            else:
                print(f"Failed to write updated CSV file '{args.csv_file}'.")

if __name__ == "__main__":
    main()
