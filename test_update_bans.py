import unittest
from unittest.mock import patch

import update_bans


class PublicHolidayFeedTests(unittest.TestCase):
    def test_public_holidays_are_not_emitted_as_truck_bans(self):
        holidays = [
            {
                "date": "2026-01-01",
                "localName": "Nieuwjaar",
                "name": "New Year's Day",
            }
        ]

        country_data = update_bans.build_country_data("BE", 2026, holidays)

        self.assertEqual(
            country_data["public_holidays"],
            [{"date": "2026-01-01", "name": "Nieuwjaar"}],
        )
        self.assertEqual(country_data["holiday_bans"], [])

    def test_legacy_country_schedules_are_not_exported_for_any_eu_country(self):
        country_codes = [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
            "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
            "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
        ]
        for code in country_codes:
            with self.subTest(country=code):
                country_data = update_bans.build_country_data(code, 2027, [])
                metadata = update_bans.get_country_metadata(code, 2027)
                self.assertEqual(country_data["timezone"], metadata["timezone"])
                self.assertNotIn("standard_weekend_ban", country_data)
                self.assertNotIn("summer_ban", country_data)
                self.assertNotIn("night_ban", country_data)
                self.assertNotIn("regional_note", country_data)

    def test_verified_polish_summer_schedule_is_preserved(self):
        schedule = {
            "active": True,
            "period": "2027-06-25 to 2027-08-31",
            "days": ["Friday", "Saturday", "Sunday"],
            "time": "Pá 18-22, So 08-14, Ne 08-22",
            "verified": True,
            "scope": "national",
            "source_url": "https://gov.pl/web/infrastruktura/holiday-restrictions",
        }
        with patch.dict(
            update_bans.VERIFIED_POLISH_SUMMER_BANS,
            {2027: schedule},
            clear=True,
        ):
            metadata = update_bans.get_country_metadata("PL", 2027)

        self.assertEqual(metadata["rules"]["summer_ban"], schedule)

    def test_only_verified_national_records_with_https_sources_are_emitted(self):
        record = {
            "date": "2026-10-28",
            "name": "Statehood Day",
            "time": "13:00 - 22:00",
            "ban": True,
            "verified": True,
            "scope": "national",
            "source_url": "https://example.gov/transport-law",
        }
        with patch.dict(
            update_bans.VERIFIED_HOLIDAY_BANS,
            {("CZ", 2026): [record]},
            clear=True,
        ):
            country_data = update_bans.build_country_data("CZ", 2026, [])

        self.assertEqual(country_data["holiday_bans"], [record])

    def test_rejects_non_https_or_unverified_holiday_ban_records(self):
        record = {
            "date": "2026-10-28",
            "name": "Statehood Day",
            "time": "13:00 - 22:00",
            "ban": True,
            "verified": True,
            "scope": "national",
            "source_url": "http://example.gov/transport-law",
        }
        with patch.dict(
            update_bans.VERIFIED_HOLIDAY_BANS,
            {("CZ", 2026): [record]},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                update_bans.get_verified_holiday_bans("CZ", 2026)


if __name__ == "__main__":
    unittest.main()
