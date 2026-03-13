python

#!/usr/bin/env python3
"""
Basic Microphone Checker - HCF4051BE + 5x INMP441
Tests all microphones and shows levels
"""

import numpy as np
import time
import RPi.GPIO as GPIO
import sounddevice as sd

def test_microphones():
    print("🎤 MICROPHONE WORKING TEST")
    print("=" * 40)
    print("This will test all 5 microphones one by one.")
    print("Make noise when each microphone is tested!")
    print()
    
    # GPIO setup for HCF4051BE
    pins = {'A': 5, 'B': 6, 'C': 13, 'INH': 19}
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all GPIO pins
        for pin_name, pin_num in pins.items():
            GPIO.setup(pin_num, GPIO.OUT)
            GPIO.output(pin_num, GPIO.LOW)
        
        print("✅ GPIO pins setup complete")
        
        # Microphone info
        mics = {
            0: "Reference",
            1: "Quadrant 1", 
            2: "Quadrant 2",
            3: "Quadrant 3",
            4: "Quadrant 4"
        }
        
        results = {}
        
        # Test each microphone
        for channel in range(5):
            print(f"\n🎤 Testing {mics[channel]} (Channel {channel})")
            print("Make noise now!")
            
            # Select channel
            GPIO.output(pins['INH'], GPIO.LOW)  # Enable
            GPIO.output(pins['A'], (channel >> 0) & 1)  # A0
            GPIO.output(pins['B'], (channel >> 1) & 1)  # A1
            GPIO.output(pins['C'], (channel >> 2) & 1)  # A2
            
            time.sleep(0.05)  # Settle
            
            # Record audio
            try:
                print("  Recording 3 seconds...")
                audio = sd.rec(144000, samplerate=48000, channels=1, dtype='int32')
                sd.wait()
                
                # Calculate audio levels
                audio_list = audio.flatten()
                positive_values = [abs(x) for x in audio_list if abs(x) > 100]
                
                if positive_values:
                    rms = (sum([x*x for x in positive_values]) / len(positive_values)) ** 0.5
                    max_level = max(abs(x) for x in audio_list)
                else:
                    rms = 0
                    max_level = 0
                
                print(f"  📊 Levels: RMS={rms:.0f}, Peak={max_level}")
                
                # Determine if working
                if rms > 100:
                    print(f"  ✅ {mics[channel]}: WORKING")
                    results[channel] = "✅ WORKING"
                elif rms > 20:
                    print(f"  ⚠️  {mics[channel]}: Weak signal")
                    results[channel] = "⚠️ WEAK"
                else:
                    print(f"  ❌ {mics[channel]}: No signal")
                    results[channel] = "❌ FAILED"
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results[channel] = "❌ ERROR"
            
            # Disable multiplexer
            GPIO.output(pins['INH'], GPIO.HIGH)
            
            if channel < 4:
                input("Press Enter for next microphone...")
        
        # Final summary
        print("\n" + "="*50)
        print("📋 FINAL RESULTS")
        print("="*50)
        
        for channel, status in results.items():
            print(f"{mics[channel]:<15}: {status}")
        
        working_count = sum(1 for status in results.values() if "✅" in status)
        print(f"\nSUMMARY: {working_count}/5 microphones working")
        
        if working_count == 5:
            print("🎉 ALL MICROPHONES WORKING!")
        elif working_count >= 3:
            print("⚠️  Some microphones working")
        else:
            print("🚨 Most microphones failed - check connections")
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
    
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_microphones()
    input("\nPress Enter to exit...")
