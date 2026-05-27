import time
import os
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

# Auto-detect I2C bus (Raspberry Pi 5 uses 13 or 14, older models use 1)
def find_i2c_bus():
    """Find available I2C bus"""
    bus_candidates = [1, 13, 14, 0]
    for bus_num in bus_candidates:
        if os.path.exists(f'/dev/i2c-{bus_num}'):
            return bus_num
    return 1  # Default fallback

# Get the correct I2C bus
i2c_bus = find_i2c_bus()
print(f"Using I2C bus: {i2c_bus}")

# Create an MPU9250 instance
try:
    mpu = MPU9250(
        address_ak=AK8963_ADDRESS,
        address_mpu_master=MPU9050_ADDRESS_68,
        address_mpu_slave=None,
        bus=i2c_bus,
        gfs=GFS_1000,
        afs=AFS_8G,
        mfs=AK8963_BIT_16,
        mode=AK8963_MODE_C100HZ
    )
    
    # Configure the MPU9250 (with error handling for magnetometer)
    try:
        mpu.configure()
        magnetometer_available = True
        print("MPU-9250 configured successfully (with magnetometer)")
    except Exception as e:
        print(f"Warning: Magnetometer configuration failed: {e}")
        print("Continuing with accelerometer and gyroscope only...")
        magnetometer_available = False
        # Try to configure without magnetometer
        try:
            # Configure MPU-9250 core (accelerometer and gyroscope)
            mpu.writeMPU(0x6B, 0x00)  # Wake up
            mpu.writeMPU(0x1C, 0x10)  # Accel config ±8g
            mpu.writeMPU(0x1B, 0x10)  # Gyro config ±1000°/s
            print("MPU-9250 core configured (accelerometer + gyroscope)")
        except Exception as e2:
            print(f"Error configuring MPU-9250: {e2}")
            raise

except Exception as e:
    print(f"Failed to initialize MPU-9250: {e}")
    print("\nTroubleshooting:")
    print("1. Check I2C is enabled: sudo raspi-config")
    print("2. Verify sensor wiring:")
    print("   - VCC → 3.3V (Pin 1 or 17)")
    print("   - GND → Ground")
    print("   - SDA → GPIO 2 (Pin 3)")
    print("   - SCL → GPIO 3 (Pin 5)")
    print("3. Check sensor detection: sudo i2cdetect -y 13")
    exit(1)

print("\nReading sensor data. Press Ctrl+C to stop.\n")
print("=" * 60)

try:
    while True:
        # Clear screen
        os.system('clear')
        
        # Print header
        print("=" * 60)
        print("MPU-9250 Sensor Data Visualization")
        print("=" * 60)
        print()
        
        try:
            # Read the accelerometer and gyroscope values
            accel_data = mpu.readAccelerometerMaster()
            gyro_data = mpu.readGyroscopeMaster()
            
            # Print accelerometer data
            print("ACCELEROMETER (m/s²)")
            print(f"  X-axis: {accel_data[0]:8.3f} m/s²")
            print(f"  Y-axis: {accel_data[1]:8.3f} m/s²")
            print(f"  Z-axis: {accel_data[2]:8.3f} m/s²")
            print(f"  Magnitude: {(accel_data[0]**2 + accel_data[1]**2 + accel_data[2]**2)**0.5:8.3f} m/s²")
            print()
            
            # Print gyroscope data
            print("GYROSCOPE (°/s)")
            print(f"  X-axis: {gyro_data[0]:8.2f} °/s")
            print(f"  Y-axis: {gyro_data[1]:8.2f} °/s")
            print(f"  Z-axis: {gyro_data[2]:8.2f} °/s")
            print(f"  Magnitude: {(gyro_data[0]**2 + gyro_data[1]**2 + gyro_data[2]**2)**0.5:8.2f} °/s")
            print()
            
            # Try to read magnetometer (may fail)
            if magnetometer_available:
                try:
                    mag_data = mpu.readMagnetometerMaster()
                    print("MAGNETOMETER (μT)")
                    print(f"  X-axis: {mag_data[0]:8.2f} μT")
                    print(f"  Y-axis: {mag_data[1]:8.2f} μT")
                    print(f"  Z-axis: {mag_data[2]:8.2f} μT")
                    print(f"  Magnitude: {(mag_data[0]**2 + mag_data[1]**2 + mag_data[2]**2)**0.5:8.2f} μT")
                except Exception as e:
                    print("MAGNETOMETER (μT)")
                    print(f"  Error reading: {e}")
            else:
                print("MAGNETOMETER (μT)")
                print("  Not available (configuration failed)")
            
            print()
            print("=" * 60)
            print("Press Ctrl+C to stop")
            
        except Exception as e:
            print(f"Error reading sensor data: {e}")
        
        # Wait before next reading
        time.sleep(0.5)  # Update every 0.5 seconds

except KeyboardInterrupt:
    print("\n\nStopping...")
    print("Done.")
