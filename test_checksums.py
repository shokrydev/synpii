#!/usr/bin/env python3
"""Validate SynPII checksums against Presidio recognizers.

This test verifies that all generated identifiers pass Presidio's
checksum validation, ensuring compatibility for benchmarking.
"""

import sys
from pathlib import Path

# Add parent to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_kvnr_checksum():
    """Test KVNR checksum matches Presidio validation."""
    print("Testing KVNR checksum...")
    from synpii.generators.identifier import KVNRGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeKvnrRecognizer,
    )

    generator = KVNRGenerator()
    recognizer = DeKvnrRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        kvnr = entity.value
        if recognizer.validate_result(kvnr):
            passed += 1
        else:
            print(f"  FAILED: {kvnr}")

    print(f"  ✓ KVNR: {passed}/100 passed")
    return passed == 100


def test_lanr_checksum():
    """Test LANR checksum matches Presidio validation."""
    print("Testing LANR checksum...")
    from synpii.generators.identifier import LANRGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeLanrRecognizer,
    )

    generator = LANRGenerator()
    recognizer = DeLanrRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        lanr = entity.value
        if recognizer.validate_result(lanr):
            passed += 1
        else:
            print(f"  FAILED: {lanr}")

    print(f"  ✓ LANR: {passed}/100 passed")
    return passed == 100


def test_bsnr_checksum():
    """Test BSNR format matches Presidio validation."""
    print("Testing BSNR format...")
    from synpii.generators.identifier import BSNRGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeBsnrRecognizer,
    )

    generator = BSNRGenerator()
    recognizer = DeBsnrRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        bsnr = entity.value
        result = recognizer.validate_result(bsnr)
        # BSNR returns True or None (not False for valid KV codes)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {bsnr}")

    print(f"  ✓ BSNR: {passed}/100 passed")
    return passed == 100


def test_tax_id_checksum():
    """Test Tax ID checksum matches Presidio validation."""
    print("Testing Tax ID checksum...")
    from synpii.generators.identifier import TaxIDGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeTaxIdRecognizer,
    )

    generator = TaxIDGenerator()
    recognizer = DeTaxIdRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        tax_id = entity.value
        if recognizer.validate_result(tax_id):
            passed += 1
        else:
            print(f"  FAILED: {tax_id}")

    print(f"  ✓ Tax ID: {passed}/100 passed")
    return passed == 100


def test_personal_id_checksum():
    """Test Personal ID checksum matches Presidio validation."""
    print("Testing Personal ID checksum...")
    from synpii.generators.identifier import PersonalIDGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DePersonalIdRecognizer,
    )

    generator = PersonalIDGenerator()
    recognizer = DePersonalIdRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        personal_id = entity.value
        result = recognizer.validate_result(personal_id)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {personal_id}")

    print(f"  ✓ Personal ID: {passed}/100 passed")
    return passed == 100


def test_social_security_checksum():
    """Test Social Security checksum matches Presidio validation."""
    print("Testing Social Security checksum...")
    from synpii.generators.identifier import SocialSecurityGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeSocialSecurityRecognizer,
    )

    generator = SocialSecurityGenerator()
    recognizer = DeSocialSecurityRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        svnr = entity.value
        result = recognizer.validate_result(svnr)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {svnr}")

    print(f"  ✓ Social Security: {passed}/100 passed")
    return passed == 100


def test_passport_checksum():
    """Test Passport checksum matches Presidio validation."""
    print("Testing Passport checksum...")
    from synpii.generators.identifier import PassportGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DePassportRecognizer,
    )

    generator = PassportGenerator()
    recognizer = DePassportRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        passport = entity.value
        result = recognizer.validate_result(passport)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {passport}")

    print(f"  ✓ Passport: {passed}/100 passed")
    return passed == 100


def test_driver_license_format():
    """Test Driver License format matches Presidio validation."""
    print("Testing Driver License format...")
    from synpii.generators.identifier import DriverLicenseGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeDriverLicenseRecognizer,
    )

    generator = DriverLicenseGenerator()
    recognizer = DeDriverLicenseRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        license_num = entity.value
        result = recognizer.validate_result(license_num)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {license_num}")

    print(f"  ✓ Driver License: {passed}/100 passed")
    return passed == 100


def test_license_plate_format():
    """Test License Plate format matches Presidio validation."""
    print("Testing License Plate format...")
    from synpii.generators.identifier import LicensePlateGenerator
    from presidio_analyzer.predefined_recognizers.country_specific.germany import (
        DeLicensePlateRecognizer,
    )

    generator = LicensePlateGenerator()
    recognizer = DeLicensePlateRecognizer()

    passed = 0
    for i in range(100):
        entity = generator.generate()
        plate = entity.value
        result = recognizer.validate_result(plate)
        if result is not False:
            passed += 1
        else:
            print(f"  FAILED: {plate}")

    print(f"  ✓ License Plate: {passed}/100 passed")
    return passed == 100


def main():
    """Run all checksum validation tests."""
    print("=" * 60)
    print("SynPII Checksum Validation (vs Presidio Recognizers)")
    print("=" * 60 + "\n")

    tests = [
        test_kvnr_checksum,
        test_lanr_checksum,
        test_bsnr_checksum,
        test_tax_id_checksum,
        test_personal_id_checksum,
        test_social_security_checksum,
        test_passport_checksum,
        test_driver_license_format,
        test_license_plate_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}")
            print(f"  {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
