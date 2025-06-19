import unittest
import json
import tempfile
import os
import datetime # Added
from unittest.mock import patch # Added
from click.testing import CliRunner
from collections import defaultdict

# Assuming 'fsr.cli:cli' is the entry point for the main CLI application.
# We will continue to test via CLI runner for end-to-end command testing.

# User-provided JSON string for May 2025 test (full version)
USER_PROVIDED_JSON_MAY_2025_STR = """
{
  "congregation": {
    "id": 28341,
    "number": 1859,
    "name": "East Karenberg Area Congregation (#744)",
    "locales_id": 37,
    "timezones_id": 95,
    "countries_id": 58,
    "registered_at": "2022-12-25T00:29:45Z",
    "abandonedreminder": null,
    "abandonedremindercount": 0,
    "lastreminder": "2025-06-03T13:06:04Z",
    "address": "9803 Cook Skyway, South Teresaton, MA 63163",
    "phone": "374-790-9425x989",
    "guid": "ec5a7bdf-aff8-4871-a1ec-108646376155",
    "wmdow": 7,
    "wmtime": "10:15:00",
    "mmdow": 5,
    "mmtime": "17:00:00",
    "wmdow_future": null,
    "wmtime_future": null,
    "mmdow_future": null,
    "mmtime_future": null,
    "future_start_date": null,
    "last_updated": "2025-06-11T20:13:31Z",
    "unmanaged": false,
    "jworg_not_found": false,
    "jworg_skip": false,
    "kind": "cong",
    "jworg_langcode": "FR",
    "jworg_location": {
      "OrbPoint": [
        -72.66801,
        19.47254
      ],
      "srid": 4326,
      "valid": true
    },
    "circuit_id": null,
    "country": {
      "id": 58,
      "code": "FR",
      "name": "Canada",
      "datefmt": "dd-mm-yyyy",
      "namefmt": "last",
      "addrfmt": "pc",
      "paper_size": "letter"
    },
    "timezone": {
      "id": 95,
      "name": "America/New-York",
      "offset": "-05:00",
      "countrycode": "FR"
    },
    "locale": {
      "id": 37,
      "code": "fr",
      "name": "French",
      "symbol": "FR"
    }
  },
  "publishers": [
    {
      "id": 1000001,
      "uuid": "2993edd6-f588-48b7-a337-bf4c6c859c86",
      "firstname": "Michael",
      "lastname": "Edwards",
      "middlename": null,
      "sex": "Male",
      "birth": "1955-07-22",
      "baptism": "2004-01-31",
      "pioneerid": null,
      "appt": "Assigned Role Gamma-8",
      "email": "qavery@example.org",
      "cellphone": "001-287-965-0666",
      "homephone": "200-523-6790x9933",
      "otherphone": null,
      "address_id": 1623950,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148617,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-D",
      "suffix": null,
      "descriptor": null,
      "loginemail": "carterderek@example.org",
      "lastlogin": "2024-07-13T22:23:01Z",
      "lastmobiletoken": "2024-09-16T17:27:28Z",
      "emailbounce": false,
      "locales_id": 37,
      "revoked": false,
      "anointed": true,
      "familycontact": true,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": true,
      "appleauth": false,
      "sgo": true,
      "locale": "fr",
      "permissionusergroups": [
        {
          "id": 779083,
          "user_id": 1000001,
          "group_id": 1
        }
      ],
      "emergencycontacts": [
        {
          "id": 440170,
          "name": "Steven Brown",
          "line1": "730 Sanchez Station Apt. 982",
          "line2": null,
          "city": "West Anne",
          "state": "CA",
          "postalcode": "54795",
          "country": "Burundi",
          "email": "jamesscott@example.com",
          "cellphone": "(254)370-8227x34680",
          "homephone": null,
          "otherphone": "001-956-477-4522x3411",
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        },
        {
          "id": 440171,
          "name": "Austin Montgomery",
          "line1": "681 Woodward Parks",
          "line2": null,
          "city": "Lake Connor",
          "state": "CO",
          "postalcode": null,
          "country": "Argentina",
          "email": null,
          "cellphone": "(832)458-5507",
          "homephone": null,
          "otherphone": "001-572-784-8796x03469",
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000002,
      "uuid": "3a1ba153-d260-4d3f-a5d2-0f24fdfc88f1",
      "firstname": "Brenda",
      "lastname": "Moore",
      "middlename": null,
      "sex": "Female",
      "birth": "1946-05-01",
      "baptism": "1958-08-21",
      "pioneerid": null,
      "appt": null,
      "email": "bmccoy@example.org",
      "cellphone": "351.600.8635",
      "homephone": "614-660-4339x59512",
      "otherphone": null,
      "address_id": 1593837,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148616,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-G",
      "suffix": null,
      "descriptor": null,
      "loginemail": "kimhiggins@example.org",
      "lastlogin": "2024-06-10T01:53:08Z",
      "lastmobiletoken": "2025-01-30T14:50:45Z",
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": true,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 427562,
          "name": "Julia Bauer",
          "line1": "924 Andrea Squares",
          "line2": "Suite 440",
          "city": null,
          "state": null,
          "postalcode": null,
          "country": null,
          "email": null,
          "cellphone": "290-769-9113",
          "homephone": "285-987-1942",
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        },
        {
          "id": 427563,
          "name": "Mrs. Lindsey Webster MD",
          "line1": null,
          "line2": "Apt. 913",
          "city": null,
          "state": null,
          "postalcode": null,
          "country": null,
          "email": null,
          "cellphone": "001-827-559-3617",
          "homephone": "001-703-586-6564x13109",
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000003,
      "uuid": "2ecc72ac-f685-4b5c-b651-d608be79ea49",
      "firstname": "Anna",
      "lastname": "Bishop",
      "middlename": null,
      "sex": "Female",
      "birth": "1974-08-16",
      "baptism": "2011-04-01",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "001-314-743-1388x70034",
      "homephone": null,
      "otherphone": null,
      "address_id": 1593838,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148619,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-K",
      "suffix": null,
      "descriptor": null,
      "loginemail": null,
      "lastlogin": null,
      "lastmobiletoken": "2025-01-07T10:48:53Z",
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": false,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 427765,
          "name": "Angela Burke",
          "line1": "779 Tyler Wall",
          "line2": null,
          "city": "Jacobburgh",
          "state": "KS",
          "postalcode": null,
          "country": "Reunion",
          "email": null,
          "cellphone": null,
          "homephone": "001-684-376-4777x80513",
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000004,
      "uuid": "b33e9ea0-5e0e-40b4-8656-2bf844fbb00f",
      "firstname": "Gail",
      "lastname": "Jones",
      "middlename": null,
      "sex": "Female",
      "birth": "1948-08-11",
      "baptism": "1969-05-26",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "8273709215",
      "homephone": null,
      "otherphone": null,
      "address_id": 1593838,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148619,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-Y",
      "suffix": null,
      "descriptor": null,
      "loginemail": null,
      "lastlogin": null,
      "lastmobiletoken": "2025-02-27T11:51:45Z",
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": false,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 427766,
          "name": "Jordan Moore",
          "line1": "35934 Yang Burg",
          "line2": null,
          "city": "Jonview",
          "state": null,
          "postalcode": null,
          "country": "Uruguay",
          "email": null,
          "cellphone": "5072413188",
          "homephone": null,
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": false,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000005,
      "uuid": "3d2edc76-c41f-4e36-a17c-e06433c2afce",
      "firstname": "Dawn",
      "lastname": "Berry",
      "middlename": null,
      "sex": "Female",
      "birth": "2004-12-18",
      "baptism": "2020-08-13",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "001-549-706-9266x37032",
      "homephone": "+1-207-241-6630x2220",
      "otherphone": null,
      "address_id": 1593839,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148619,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-E",
      "suffix": null,
      "descriptor": null,
      "loginemail": "rosssandra@example.org",
      "lastlogin": null,
      "lastmobiletoken": "2024-11-29T10:25:23Z",
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": true,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 428709,
          "name": "Allison Gonzalez",
          "line1": "01144 Eric Dam Suite 750",
          "line2": null,
          "city": "East Dennisshire",
          "state": "CO",
          "postalcode": null,
          "country": "Congo",
          "email": null,
          "cellphone": "827.670.9020x2192",
          "homephone": null,
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000006,
      "uuid": "5850fdd5-cb7d-4fb1-b43c-5acdf834c83e",
      "firstname": "Alicia",
      "lastname": "Fitzgerald",
      "middlename": null,
      "sex": "Female",
      "birth": "2001-10-16",
      "baptism": "2023-08-14",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "+1-606-879-5831",
      "homephone": null,
      "otherphone": null,
      "address_id": 1593841,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148617,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Inactive-X",
      "suffix": null,
      "descriptor": null,
      "loginemail": null,
      "lastlogin": null,
      "lastmobiletoken": "2024-09-23T09:30:52Z",
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": false,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 440163,
          "name": "Travis Todd",
          "line1": "3194 Lewis Stravenue",
          "line2": null,
          "city": null,
          "state": null,
          "postalcode": null,
          "country": "Turkmenistan",
          "email": null,
          "cellphone": "001-970-472-5542x7683",
          "homephone": null,
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": "2025-06-08T14:35:36Z",
      "tags": []
    },
    {
      "id": 1000007,
      "uuid": "b484b4f2-067d-44a5-bb67-92d25e670fdd",
      "firstname": "Sierra",
      "lastname": "Johnson",
      "middlename": null,
      "sex": "Female",
      "birth": "1977-06-17",
      "baptism": "2017-12-21",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "+1-950-631-9355x420",
      "homephone": null,
      "otherphone": null,
      "address_id": null,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148619,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Pending-S",
      "suffix": null,
      "descriptor": null,
      "loginemail": null,
      "lastlogin": null,
      "lastmobiletoken": null,
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": false,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 427543,
          "name": "Jonathan Clarke",
          "line1": "920 Ferguson Walks",
          "line2": null,
          "city": "Blackport",
          "state": "TX",
          "postalcode": null,
          "country": "Bhutan",
          "email": null,
          "cellphone": null,
          "homephone": "768-563-5166x0341",
          "otherphone": "930-985-8526x06421",
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": false,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000008,
      "uuid": "41b5793f-05d8-4c1f-bcf6-1a7ea6ad9b0f",
      "firstname": "Kaitlin",
      "lastname": "Todd",
      "middlename": null,
      "sex": "Female",
      "birth": "1975-05-15",
      "baptism": "1998-11-21",
      "pioneerid": null,
      "appt": null,
      "email": "hnielsen@example.org",
      "cellphone": "582.742.0833x2488",
      "homephone": "+1-438-549-9794x91415",
      "otherphone": null,
      "address_id": 1593842,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148617,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Active-J",
      "suffix": null,
      "descriptor": null,
      "loginemail": "cayala@example.com",
      "lastlogin": null,
      "lastmobiletoken": "2025-05-02T21:12:28Z",
      "emailbounce": false,
      "locales_id": 37,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": false,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": true,
      "appleauth": false,
      "sgo": false,
      "locale": "fr",
      "emergencycontacts": [
        {
          "id": 440177,
          "name": "Catherine Cooke",
          "line1": null,
          "line2": null,
          "city": "Brianport",
          "state": "FM",
          "postalcode": "57956",
          "country": "Liberia",
          "email": null,
          "cellphone": "345.961.3561",
          "homephone": null,
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000009,
      "uuid": "9a5c9fb0-54f3-4dd5-91bf-1183313b45f3",
      "firstname": "Troy",
      "lastname": "Bush",
      "middlename": null,
      "sex": "Male",
      "birth": "1963-07-08",
      "baptism": "2000-07-19",
      "pioneerid": null,
      "appt": null,
      "email": "freemanmorgan@example.net",
      "cellphone": "(961)537-0779x2697",
      "homephone": null,
      "otherphone": null,
      "address_id": null,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148617,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Inactive-P",
      "suffix": null,
      "descriptor": null,
      "loginemail": "ronald70@example.net",
      "lastlogin": "2023-12-17T15:36:06Z",
      "lastmobiletoken": "2025-06-01T05:58:56Z",
      "emailbounce": false,
      "locales_id": 7,
      "revoked": false,
      "anointed": false,
      "familycontact": true,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": true,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": true,
      "appleauth": false,
      "sgo": false,
      "locale": "fr",
      "emergencycontacts": [
        {
          "id": 439517,
          "name": "Melissa Alexander",
          "line1": null,
          "line2": null,
          "city": null,
          "state": null,
          "postalcode": null,
          "country": null,
          "email": null,
          "cellphone": "(400)571-3174",
          "homephone": null,
          "otherphone": null,
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": true,
      "pubinvite": null,
      "tags": []
    },
    {
      "id": 1000010,
      "uuid": "9e2e13ba-eb6e-4096-b11f-bc4bb377b0af",
      "firstname": "Kiara",
      "lastname": "Cross",
      "middlename": null,
      "sex": "Female",
      "birth": "1967-10-04",
      "baptism": "2022-11-16",
      "pioneerid": null,
      "appt": null,
      "email": null,
      "cellphone": "(926)275-7860",
      "homephone": null,
      "otherphone": null,
      "address_id": null,
      "comments": null,
      "congregations_id": 28341,
      "group_id": 148617,
      "language_group_id": null,
      "firstmonth": null,
      "status": "Membership Status Inactive-V",
      "suffix": null,
      "descriptor": null,
      "loginemail": null,
      "lastlogin": null,
      "lastmobiletoken": null,
      "emailbounce": false,
      "locales_id": null,
      "revoked": false,
      "anointed": false,
      "familycontact": false,
      "rpquota": null,
      "advdirective": false,
      "reportstobranch": true,
      "piiconsentdate": null,
      "e2e_iv": null,
      "e2e_firstname": null,
      "e2e_middlename": null,
      "e2e_lastname": null,
      "e2e_suffix": null,
      "e2e_pioneerid": null,
      "e2e_birth": null,
      "e2e_baptism": null,
      "e2e_email": null,
      "e2e_cellphone": null,
      "e2e_homephone": null,
      "e2e_otherphone": null,
      "e2e_comments": null,
      "googleauth": false,
      "appleauth": false,
      "sgo": false,
      "locale": null,
      "emergencycontacts": [
        {
          "id": 439519,
          "name": "Becky Morse",
          "line1": null,
          "line2": null,
          "city": null,
          "state": null,
          "postalcode": null,
          "country": null,
          "email": null,
          "cellphone": "001-349-749-7120x7391",
          "homephone": "001-444-467-4770",
          "otherphone": "(868)764-9188",
          "comments": null,
          "e2e_iv": null,
          "e2e_name": null,
          "e2e_line1": null,
          "e2e_line2": null,
          "e2e_city": null,
          "e2e_state": null,
          "e2e_postalcode": null,
          "e2e_country": null,
          "e2e_email": null,
          "e2e_cellphone": null,
          "e2e_homephone": null,
          "e2e_otherphone": null,
          "e2e_comments": null
        }
      ],
      "mobilepush": false,
      "pubinvite": null,
      "tags": []
    }
  ],
  "addresses": [],
  "fsGroups": [],
  "attendance": {
    "attendance": [
      {
        "id": 676391,
        "month": "2025-05",
        "attendanceGroupId": 0,
        "mw1": 118,
        "mw2": 142,
        "mw3": 133,
        "mw4": 131,
        "mw5": 137,
        "mwAvg": 132,
        "mwCount": 5,
        "mwTotal": 661,
        "we1": 170,
        "we2": 158,
        "we3": 153,
        "we4": 169,
        "weAvg": 163,
        "weCount": 4,
        "weTotal": 650
      }
    ],
    "attendanceGroups": [
      {
        "id": 0,
        "name": ""
      }
    ]
  },
  "reports": [
    {
      "id": 75950475, "user": {"id": 1000001}, "month": 5, "year": 2025, "minutes_as_hours": "39", "minutes": 2340, "pioneer": "Regular", "studies": 6, "remarks": null, "submitted_month": null, "reported_at": "2024-07-23T05:46:06Z", "reported_by": 1000001, "has_reported_field_service": true
    },
    {
      "id": 75961958, "user": {"id": 1000002}, "month": 5, "year": 2025, "minutes_as_hours": "55", "minutes": 3300, "pioneer": "Regular", "studies": 6, "remarks": null, "submitted_month": null, "reported_at": "2025-04-10T21:57:25Z", "reported_by": 1000002, "has_reported_field_service": true
    },
    {
      "id": 76199897, "user": {"id": 1000003}, "month": 5, "year": 2025, "minutes_as_hours": "64", "minutes": 3840, "pioneer": "Regular", "studies": 4, "remarks": null, "submitted_month": null, "reported_at": "2024-08-22T03:01:16Z", "reported_by": 1000003, "has_reported_field_service": true
    },
    {
      "id": 76218222, "user": {"id": 1000004}, "month": 5, "year": 2025, "minutes_as_hours": "66", "minutes": 3960, "pioneer": "Regular", "studies": 5, "remarks": null, "submitted_month": null, "reported_at": "2025-04-09T00:42:26Z", "reported_by": 1000004, "has_reported_field_service": true
    },
    {
      "id": 76206180, "user": {"id": 1000005}, "month": 5, "year": 2025, "minutes_as_hours": "60", "minutes": 3600, "pioneer": "Regular", "studies": 8, "remarks": null, "submitted_month": null, "reported_at": "2025-06-15T16:02:31Z", "reported_by": 1000034, "has_reported_field_service": true
    },
    {
      "id": 76034209, "user": {"id": 1000006}, "month": 5, "year": 2025, "minutes_as_hours": "55", "minutes": 3300, "pioneer": "Regular", "studies": 8, "remarks": null, "submitted_month": null, "reported_at": "2024-10-04T13:45:08Z", "reported_by": 1000006, "has_reported_field_service": true
    },
    {
      "id": 76116601, "user": {"id": 1000007}, "month": 5, "year": 2025, "minutes_as_hours": "53", "minutes": 3180, "pioneer": "Regular", "studies": 6, "remarks": null, "submitted_month": null, "reported_at": "2024-12-12T06:01:13Z", "reported_by": 1000055, "has_reported_field_service": true
    },
    {
      "id": 75950104, "user": {"id": 1000008}, "month": 5, "year": 2025, "minutes_as_hours": "50", "minutes": 3000, "pioneer": "Regular", "studies": 3, "remarks": null, "submitted_month": null, "reported_at": "2025-05-15T23:39:58Z", "reported_by": 1000008, "has_reported_field_service": true
    },
    {
      "id": 75707426, "user": {"id": 1000009}, "month": 5, "year": 2025, "minutes_as_hours": "0.02", "minutes": 1, "pioneer": null, "studies": 15, "remarks": "Whose newspaper tax compare blood whose hold remember moment five exist continue.", "submitted_month": null, "reported_at": "2024-11-24T17:27:10Z", "reported_by": 1000009, "has_reported_field_service": true
    },
    {
      "id": 74602239, "user": {"id": 1000010}, "month": 5, "year": 2025, "minutes_as_hours": "0.02", "minutes": 1, "pioneer": null, "studies": 14, "remarks": null, "submitted_month": null, "reported_at": "2025-02-14T06:53:07Z", "reported_by": 1000009, "has_reported_field_service": true
    }
  ],
  "notPublishers": [],
  "monthlyTotals": []
}
"""

class TestMonthlyActivityReport(unittest.TestCase):
    user_provided_json_data_may_2025_str = USER_PROVIDED_JSON_MAY_2025_STR

    MAY_2026_MOCK_DATA_STR = """
{
  "congregation": {
    "id": 28342, "name": "Default Test Cong", "locales_id": 37,
    "country": {"id": 58, "code": "FR", "name": "Canada", "datefmt": "dd-mm-yyyy", "namefmt": "last", "addrfmt": "pc", "paper_size": "letter"},
    "timezone": {"id": 95, "name": "America/New-York", "offset": "-05:00", "countrycode": "FR"},
    "locale": {"id": 37, "code": "fr", "name": "French", "symbol": "FR"}
  },
  "publishers": [
    {"id": "rp1", "firstname": "RP", "lastname": "One", "status": "Membership Status Active-A"},
    {"id": "rp2", "firstname": "RP", "lastname": "Two", "status": "Membership Status Active-B"},
    {"id": "ap1", "firstname": "AP", "lastname": "One", "status": "Membership Status Active-C"},
    {"id": "pub1", "firstname": "Pub", "lastname": "One", "status": "Membership Status Active-D"},
    {"id": "pub2", "firstname": "Pub", "lastname": "Two", "status": "Membership Status Active-E"},
    {"id": "pub3", "firstname": "Pub", "lastname": "Three", "status": "Membership Status Active-F"},
    {"id": "sp1", "firstname": "SP", "lastname": "One", "status": "Membership Status Active-G"},
    {"id": "inactive1", "firstname": "Inactive", "lastname": "One", "status": "Membership Status Inactive-A"}
  ],
  "reports": [
    {"user": {"id": "rp1"}, "year": 2026, "month": 5, "minutes": 3000, "studies": 5, "pioneer": "Regular", "has_reported_field_service": true},
    {"user": {"id": "rp2"}, "year": 2026, "month": 5, "minutes": 3600, "studies": 4, "pioneer": "Regular", "has_reported_field_service": true},
    {"user": {"id": "ap1"}, "year": 2026, "month": 5, "minutes": 1800, "studies": 3, "pioneer": "Auxiliary", "has_reported_field_service": true},
    {"user": {"id": "pub1"}, "year": 2026, "month": 5, "minutes": 600, "studies": 2, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "pub2"}, "year": 2026, "month": 5, "minutes": 0, "studies": 1, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "pub3"}, "year": 2026, "month": 5, "minutes": 300, "studies": 0, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "sp1"}, "year": 2026, "month": 5, "minutes": 6000, "studies": 10, "pioneer": "Special", "reportstobranch": true, "has_reported_field_service": true}
  ],
  "attendance": {
    "attendance": [
      {"month": "2026-05", "weAvg": 100, "mwAvg": 90}
    ]
  }
}
"""

    WITH_DATA_OCT_2023_JSON_STR = """
{
  "congregation": {
    "id": 28343, "name": "With Data Test Cong", "locales_id": 37, "jworg_langcode": "HT",
    "country": {"id": 58, "code": "HT", "name": "Haiti", "datefmt": "dd-mm-yyyy", "namefmt": "last", "addrfmt": "pc", "paper_size": "letter"},
    "timezone": {"id": 95, "name": "America/Port-au-Prince", "offset": "-05:00", "countrycode": "HT"},
    "locale": {"id": 38, "code": "ht", "name": "Haitian Creole", "symbol": "HT"}
  },
  "publishers": [
    {"id": "rp_wd1", "firstname": "RPWD", "lastname": "One", "status": "Active"},
    {"id": "ap_wd1", "firstname": "APWD", "lastname": "One", "status": "Active"},
    {"id": "pub_wd1", "firstname": "PubWD", "lastname": "One", "status": "Active"},
    {"id": "pub_wd2", "firstname": "PubWD", "lastname": "Two", "status": "Active"},
    {"id": "sp_wd1", "firstname": "SPWD", "lastname": "One", "status": "Active"},
    {"id": "inactive_wd1", "firstname": "InactiveWD", "lastname": "One", "status": "Inactive"}
  ],
  "reports": [
    {"user": {"id": "rp_wd1"}, "year": 2023, "month": 10, "minutes": 3300, "studies": 3, "pioneer": "Regular", "has_reported_field_service": true},
    {"user": {"id": "ap_wd1"}, "year": 2023, "month": 10, "minutes": 2100, "studies": 2, "pioneer": "Auxiliary", "has_reported_field_service": true},
    {"user": {"id": "pub_wd1"}, "year": 2023, "month": 10, "minutes": 720, "studies": 1, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "pub_wd2"}, "year": 2023, "month": 10, "minutes": 480, "studies": 0, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "sp_wd1"}, "year": 2023, "month": 10, "minutes": 5400, "studies": 7, "pioneer": "Special", "reportstobranch": true, "has_reported_field_service": true}
  ],
  "attendance": {
    "attendance": [
      {"month": "2023-10", "weAvg": 150}
    ]
  }
}
"""

    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None # Show full diffs

        # Mock data for summaries, updated for new features
        self.mock_data_for_summaries = {
            "congregation": {},
            "publishers": [
                {"id": "1000001", "firstname": "Michael", "lastname": "Edwards"}, # Inactive
                {"id": "1000002", "firstname": "Stephanie", "lastname": "Roman"}, # Aux Pioneer
                {"id": "1000003", "firstname": "Carol", "lastname": "Mitchell"},    # Publisher
                {"id": "1000004", "firstname": "Carl", "lastname": "Smith"},       # Publisher
                {"id": "1000005", "firstname": "Jason", "lastname": "Nguyen"},     # Reg Pioneer
                {"id": "1000006", "firstname": "Gabriel", "lastname": "Williams"}, # Special Pioneer (activity excluded from summary)
                {"id": "1000007", "firstname": "Joel", "lastname": "Jenkins"},     # Aux Pioneer
                {"id": "1000008", "firstname": "Jacqueline", "lastname": "Moore"}  # Publisher (reports, 0 activity)
            ],
            "reports": [
                # Month 1: 2026-08 (Active Month)
                {"year": 2026, "month": 8, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False, "minutes": None, "studies": None},
                {"year": 2026, "month": 8, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 3000, "studies": 5}, # AP1: 50hr, 5st
                {"year": 2026, "month": 8, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": True, "minutes": 60, "studies": 1},          # Pub1: 1st
                {"year": 2026, "month": 8, "user": {"id": "1000004"}, "pioneer": "Publisher", "has_reported_field_service": True, "minutes": 120, "studies": 2},    # Pub2: 2st
                {"year": 2026, "month": 8, "user": {"id": "1000005"}, "pioneer": "Regular", "has_reported_field_service": True, "minutes": 600, "studies": None},   # RP1: 10hr, 0st
                {"year": 2026, "month": 8, "user": {"id": "1000006"}, "pioneer": "Special", "has_reported_field_service": True, "minutes": 0, "studies": 3},     # SP1: 0hr, 3st (EXCLUDED from this report)
                {"year": 2026, "month": 8, "user": {"id": "1000007"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 30, "studies": 0},      # AP2: 0hr (30min), 0st
                {"year": 2026, "month": 8, "user": {"id": "1000008"}, "pioneer": None, "has_reported_field_service": True, "minutes": 0, "studies": 0},          # Pub3: Reports, 0 activity

                # Month 2: 2026-09 (No Activity Month)
                {"year": 2026, "month": 9, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False},
                {"year": 2026, "month": 9, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 0, "studies": 0},
                {"year": 2026, "month": 9, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": False},
                {"year": 2026, "month": 9, "user": {"id": "1000006"}, "pioneer": "Special", "has_reported_field_service": False}, # SP inactive this month
            ],
            "attendance": [ # Added
                {"month": "2026-08", "mwAvg": 0, "mwCount": 0, "mwTotal": 0, "weAvg": 150, "weCount": 4, "weTotal": 600},
                {"month": "2026-09", "mwAvg": 0, "mwCount": 0, "mwTotal": 0, "weAvg": 0, "weCount": 0, "weTotal": 0}
            ]
        }

    def _run_summary_command(self, month_str: str = None): # Modified signature
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp_json_file:
            json.dump(self.mock_data_for_summaries, tmp_json_file)
            tmp_json_file_path = tmp_json_file.name
        
        cli_path = "~/.local/bin/fsr" 
        if not os.path.exists(os.path.expanduser(cli_path)):
             cli_path = "fsr"

        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity']
        if month_str:
            cmd.extend(['--month', month_str])

        result = self.runner.invoke(
            None,
            cmd, # Use the constructed cmd list
            catch_exceptions=False,
            prog_name="fsr"
        )
        os.remove(tmp_json_file_path)
        return result

    def test_monthly_activity_with_data(self):
        """Test summary for a month with various activities, ensuring Haitian Creole output."""
        
        month_to_test = "2023-10" # Using a different month for this specific test
        year_to_test_str = month_to_test[0:4]

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(self.WITH_DATA_OCT_2023_JSON_STR)
            tmp_json_file_path = tmp_json_file.name

        cli_path = "~/.local/bin/fsr"
        if not os.path.exists(os.path.expanduser(cli_path)):
            cli_path = "fsr"

        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity', '--month', month_to_test]
        # Mocking date for consistency, though with --month specified, it's less critical for date calculation
        # but might affect "Rapò kreye" line if that's part of a more holistic check later.
        with patch('fsr.reports.summaries.datetime') as mock_datetime_summaries:
            mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2023, 11, 15, 10, 0, 0) # A date after the report month
            result = self.runner.invoke(None, cmd, catch_exceptions=False, prog_name="fsr")

        try:
            self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
            output = result.output.replace("\r\n", "\n")

            # Expected Haitian Creole Output for October 2023
            expected_haitian_output = f"""RAPÒ AKTIVITE PREDIKASYON ASANBLE POU OKTÒB {year_to_test_str}

Kantite pwoklamatè................................. 5
Pyonye pèmanan.................................... 1
Pyonye oksilyè.................................... 1
Pwoklamatè........................................ 2
Total èdtan....................................... 200.00
Total etid biblik................................. 13
Mwayèn pwoklamatè ki patisipe nan ministè a chak mwa.... 5
Mwayèn èdtan chak pwoklamatè fè................... 40.00
Mwayèn etid biblik chak pwoklamatè fè............. 2.60
Kantite pwoklamatè ki lengwistik.................. 0
Tous les proclamateurs actifs..................... 5
Pyonye espesyal................................... 1
Assistance moyenne à la réunion de week-end....... 150
""".strip()

            start_of_expected_block = f"RAPÒ AKTIVITE PREDIKASYON ASANBLE POU OKTÒB {year_to_test_str}"
            if start_of_expected_block not in output:
                self.fail(f"Expected block starting with '{start_of_expected_block}' not found in output.\nOutput:\n{output}")

            actual_relevant_output = output[output.find(start_of_expected_block):].strip()
            actual_relevant_output_lines = [line for line in actual_relevant_output.split('\n') if not line.startswith("Rapò kreye:")]
            actual_relevant_output_processed = "\n".join(actual_relevant_output_lines).strip()

            self.assertEqual(actual_relevant_output_processed, expected_haitian_output,
                             f"Output does not match expected Haitian Creole summary for {month_to_test}.\nExpected:\n{expected_haitian_output}\n\nActual:\n{actual_relevant_output_processed}")

        finally:
            os.remove(tmp_json_file_path)


    def test_monthly_activity_no_activity(self):
        """Test summary for a month with no qualifying activity, new format."""
        result = self._run_summary_command("2026-09")
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        # Expected for 2026-09:
        # Pub 1000002 (Auxiliary) is active (has_reported_field_service=True) but 0 min/studies.
        # All others are inactive (has_reported_field_service=False) or Special Pioneer.
        # Total Active Publishers = 1 (1000002)
        # Attendance = 0 -> "N/A"
        # Aux Pioneers: S-4 = 1, Hours = 0, Studies = 0.
        # Other categories: S-4 = 0, Hours = 0, Studies = 0.
        # "Note: Pa gen rapò..." should NOT be present.

        self.assertIn("Tous les proclamateurs actifs\n1", output)
        self.assertIn("Assistance moyenne à la réunion de week-end\nN/A", output)

        # Proclamateurs
        proclamateurs_section = output.split("Proclamateurs")[1].split("Pionniers auxiliaires")[0]
        self.assertIn("Nombre de fiches d’activité (S-4)\n0", proclamateurs_section)
        self.assertIn("Cours bibliques\n0", proclamateurs_section)

        # Pionniers auxiliaires
        aux_section = output.split("Pionniers auxiliaires")[1].split("Pionniers permanents")[0]
        self.assertIn("Nombre de fiches d’activité (S-4)\n1", aux_section)
        self.assertIn("Heures\n0", aux_section)
        self.assertIn("Cours bibliques\n0", aux_section)

        # Pionniers permanents
        perm_section = output.split("Pionniers permanents")[1].split("\n-----------------------------")[0]
        self.assertIn("Nombre de fiches d’activité (S-4)\n0", perm_section)
        self.assertIn("Heures\n0", perm_section)
        self.assertIn("Cours bibliques\n0", perm_section)
        
        self.assertNotIn("Pyonye espesyal", output)
        self.assertNotIn("Note: Pa gen rapò ki disponib pou mwa 2026-09.", output)

    @patch('fsr.reports.summaries.datetime') # Path to datetime used in summaries.py
    def test_monthly_activity_default_month(self, mock_datetime_summaries):
        """Test summary for a default month (previous month) with Haitian Creole output."""
        # Configure mock_datetime.now() to return a date in June 2026,
        # so "previous month" defaults to May 2026.
        mock_now = datetime.datetime(2026, 6, 15, 10, 0, 0)
        mock_datetime_summaries.datetime.now.return_value = mock_now
        # Also patch datetime in data_loader if it were used for date logic there,
        # but current data_loader doesn't seem to use current date.

        expected_month_str = "2026-05"

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(self.MAY_2026_MOCK_DATA_STR) # Use the new mock data
            tmp_json_file_path = tmp_json_file.name

        cli_path = "~/.local/bin/fsr"
        if not os.path.exists(os.path.expanduser(cli_path)):
            cli_path = "fsr"

        # Invoke without --month argument
        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity']
        result = self.runner.invoke(None, cmd, catch_exceptions=False, prog_name="fsr")

        try:
            self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
            output = result.output.replace("\r\n", "\n")

            self.assertIn(f"Info: --month not provided, defaulting to previous month ({expected_month_str}).", output)

            expected_haitian_output = f"""RAPÒ AKTIVITE PREDIKASYON ASANBLE POU ME {expected_month_str[0:4]}

Kantite pwoklamatè................................. 7
Pyonye pèmanan.................................... 2
Pyonye oksilyè.................................... 1
Pwoklamatè........................................ 3
Total èdtan....................................... 255.00
Total etid biblik................................. 25
Mwayèn pwoklamatè ki patisipe nan ministè a chak mwa.... 7
Mwayèn èdtan chak pwoklamatè fè................... 36.43
Mwayèn etid biblik chak pwoklamatè fè............. 3.57
Kantite pwoklamatè ki lengwistik.................. 0
Tous les proclamateurs actifs..................... 7
Pyonye espesyal................................... 1
Assistance moyenne à la réunion de week-end....... 100
""".strip()

            start_of_expected_block = f"RAPÒ AKTIVITE PREDIKASYON ASANBLE POU ME {expected_month_str[0:4]}"
            if start_of_expected_block not in output:
                self.fail(f"Expected block starting with '{start_of_expected_block}' not found in output.\nOutput:\n{output}")

            actual_relevant_output = output[output.find(start_of_expected_block):].strip()
            # Remove dynamic "Rapò kreye:" line from actual output for comparison
            actual_relevant_output_lines = [line for line in actual_relevant_output.split('\n') if not line.startswith("Rapò kreye:")]
            actual_relevant_output_processed = "\n".join(actual_relevant_output_lines).strip()


            self.assertEqual(actual_relevant_output_processed, expected_haitian_output,
                             f"Output does not match expected Haitian Creole summary for default month.\nExpected:\n{expected_haitian_output}\n\nActual:\n{actual_relevant_output_processed}")

        finally:
            os.remove(tmp_json_file_path)


    @patch('fsr.reports.summaries.datetime') # Mock datetime module in summaries.py
    def test_monthly_activity_may_2025_haitian_creole(self, mock_datetime_summaries):
        """Tests the monthly summary report with user-provided JSON for May 2025, expecting Haitian Creole output."""

        # Mock datetime.datetime.now() specifically, as that's what summaries.py uses
        # The date of 'now' shouldn't affect this test as --month is specified,
        # but good practice if any part of report generation used current date for timestamps etc.
        # The prompt asks to mock date.today() to June 2025. We'll mock datetime.now() to a June 2025 date.
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2025, 6, 15, 10, 0, 0)


        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(self.user_provided_json_data_may_2025_str)
            tmp_json_file_path = tmp_json_file.name

        cli_path = "~/.local/bin/fsr"
        if not os.path.exists(os.path.expanduser(cli_path)):
            cli_path = "fsr"

        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity', '--month', "2025-05"]
        result = self.runner.invoke(None, cmd, catch_exceptions=False, prog_name="fsr")

        try:
            self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
            output = result.output.replace("\r\n", "\n")

            # Updated expected output for May 2025, excluding Special Pioneers from calculations
            expected_output = """RAPÒ AKTIVITE PREDIKASYON ASANBLE POU ME 2025

Kantite pwoklamatè................................. 6
Pyonye pèmanan.................................... 6
Pyonye oksilyè.................................... 0
Pwoklamatè........................................ 0
Total èdtan....................................... 334.00
Total etid biblik................................. 32
Mwayèn pwoklamatè ki patisipe nan ministè a chak mwa.... 6
Mwayèn èdtan chak pwoklamatè fè................... 55.67
Mwayèn etid biblik chak pwoklamatè fè............. 5.33
Kantite pwoklamatè ki lengwistik.................. 0
Tous les proclamateurs actifs..................... 6
Pyonye espesyal................................... 0
Assistance moyenne à la réunion de week-end....... 163
"""
            # Remove the "Rapò kreye:" line as it's dynamic
            output_lines = [line for line in output.split('\n') if not line.startswith("Rapò kreye:")]
            expected_lines = [line for line in expected_output.split('\n') if not line.startswith("Rapò kreye:")]

            # Also remove the "Info: --month not provided..." line if present (though it shouldn't be with --month)
            output_lines = [line for line in output_lines if not line.startswith("Info: --month not provided")]

            # For more robust comparison, especially if there are subtle differences in whitespace or leading/trailing newlines:
            # We compare relevant parts. The prompt asks for exact match.
            # The output from the CLI might have a title like "Rezime Rapò Aktivite Mansyèl"
            # and then "Pou Mwa: YYYY-MM" and "Rapò kreye: ..." before the main content.
            # The expected output starts directly with "RAPÒ AKTIVITE PREDIKASYON ASANBLE POU ME 2025".
            # This suggests the 'fsr summary monthly-activity' might have different output modes
            # or the provided expected output is only a specific part of the full output.
            # Given the instruction "Assert that the output matches the expected text exactly",
            # this test will likely require the `summaries.py` to be adjusted to produce this exact format.
            # For now, I will assert that the expected_text is contained within the output.
            # A more precise assertion will be needed once output format is confirmed.

            # Let's find the start of the expected block in the actual output
            start_of_expected_block = "RAPÒ AKTIVITE PREDIKASYON ASANBLE POU ME 2025"
            if start_of_expected_block not in output:
                self.fail(f"Expected block starting with '{start_of_expected_block}' not found in output.\nOutput:\n{output}")

            actual_relevant_output = output[output.find(start_of_expected_block):].strip()
            expected_relevant_output = expected_output.strip()

            self.assertEqual(actual_relevant_output, expected_relevant_output,
                             f"Output does not match expected Haitian Creole summary.\nExpected:\n{expected_relevant_output}\n\nActual:\n{actual_relevant_output}")

        finally:
            os.remove(tmp_json_file_path)
