#!/usr/bin/env python3
"""
Sensor Surface Cleaning Guide
Interactive guide for cleaning fingerprint sensor
"""

import time

def cleaning_guide():
    """Interactive sensor cleaning guide"""
    print("🧽 Fingerprint Sensor Cleaning Guide")
    print("=" * 50)
    print()
    print("Error 0x03 (Imaging Fail) is often caused by:")
    print("• Dirty or oily sensor surface")
    print("• Dust or debris on sensor")
    print("• Residue from previous use")
    print()
    
    print("🛠️ CLEANING PROCEDURE:")
    print("-" * 30)
    print()
    
    steps = [
        "1. POWER OFF the sensor system",
        "2. Gather cleaning materials:",
        "   • Soft, lint-free cloth (microfiber preferred)",
        "   • Isopropyl alcohol (70% or higher)",
        "   • Cotton swabs (optional)",
        "",
        "3. CLEAN THE SENSOR:",
        "   • Dampen cloth with isopropyl alcohol",
        "   • Gently wipe sensor surface in circular motions",
        "   • Use cotton swab for edges and crevices",
        "   • DO NOT press hard or scratch surface",
        "",
        "4. DRY COMPLETELY:",
        "   • Let alcohol evaporate completely (30 seconds)",
        "   • Ensure no moisture remains",
        "   • Surface should be completely dry",
        "",
        "5. TEST CLEAN SURFACE:",
        "   • Power on system",
        "   • Try fingerprint enrollment again",
        "   • Use clean, dry finger"
    ]
    
    for step in steps:
        print(step)
        if step.startswith(("1.", "2.", "3.", "4.", "5.")):
            input("\nPress Enter when step completed...")
            print()
    
    print("\n✅ CLEANING COMPLETE!")
    print()
    print("🧪 Now test your sensor:")
    print("python3 scripts/fingerprint_controller_optimized.py")
    print()
    print("💡 If still getting Error 0x03:")
    print("• Try different finger")
    print("• Press more firmly")
    print("• Check power supply voltage")
    print("• Run full troubleshooter:")
    print("  python3 scripts/sensor_troubleshooter.py")

if __name__ == "__main__":
    cleaning_guide()
