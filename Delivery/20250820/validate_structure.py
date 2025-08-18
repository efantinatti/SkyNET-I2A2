#!/usr/bin/env python3
"""
Validation script for SkyNET I2A2 project structure
Tests that all imports and file paths work correctly after reorganization

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import os
import sys

def validate_project_structure():
    """Validate that all required files and folders exist"""
    print("🔍 Validating project structure...")
    
    required_structure = {
        'Libs/': ['__init__.py', 'email_library.py'],
        'Config/': ['config.ini'],
        '': ['Desafio-4-RH.py', 'setup.py', 'requirements.txt', 'README_Email_Integration.md']
    }
    
    all_valid = True
    
    for folder, files in required_structure.items():
        folder_path = folder if folder else '.'
        print(f"\n📁 Checking {folder_path}:")
        
        if folder and not os.path.exists(folder):
            print(f"  ❌ Folder '{folder}' not found")
            all_valid = False
            continue
        
        for file in files:
            file_path = os.path.join(folder, file) if folder else file
            if os.path.exists(file_path):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} not found")
                all_valid = False
    
    return all_valid

def validate_imports():
    """Test that all imports work correctly"""
    print("\n🔗 Validating imports...")
    
    try:
        # Test config loading
        import configparser
        config = configparser.ConfigParser()
        config_path = 'Config/config.ini'
        if os.path.exists(config_path):
            config.read(config_path)
            print("  ✅ Config file loads successfully")
        else:
            print("  ❌ Config file not found")
            return False
        
        # Test email library import
        try:
            from Libs.email_library import EmailNotifier, send_process_completion_email
            print("  ✅ Email library imports successfully")
        except ImportError as e:
            print(f"  ❌ Email library import failed: {e}")
            return False
        
        # Test main script imports (without running it)
        try:
            import ast
            with open('Desafio-4-RH.py', 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print("  ✅ Main script syntax is valid")
        except SyntaxError as e:
            print(f"  ❌ Main script syntax error: {e}")
            return False
        except FileNotFoundError:
            print("  ❌ Main script file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import validation failed: {e}")
        return False

def validate_configuration():
    """Validate configuration file structure"""
    print("\n⚙️ Validating configuration...")
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('Config/config.ini')
        
        required_sections = ['gemini', 'email', 'validation_rules']
        required_email_keys = ['sender_email', 'sender_password', 'recipient_email']
        
        for section in required_sections:
            if section in config:
                print(f"  ✅ Section '{section}' found")
                
                if section == 'email':
                    for key in required_email_keys:
                        if key in config[section]:
                            print(f"    ✅ Key '{key}' found")
                        else:
                            print(f"    ⚠️ Key '{key}' not configured (needs user input)")
            else:
                print(f"  ❌ Section '{section}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 SkyNET I2A2 Project Structure Validation")
    print("=" * 50)
    
    # Validate structure
    structure_valid = validate_project_structure()
    
    # Validate imports
    imports_valid = validate_imports()
    
    # Validate configuration
    config_valid = validate_configuration()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY:")
    print(f"  Structure: {'✅ Valid' if structure_valid else '❌ Invalid'}")
    print(f"  Imports:   {'✅ Valid' if imports_valid else '❌ Invalid'}")
    print(f"  Config:    {'✅ Valid' if config_valid else '❌ Invalid'}")
    
    if structure_valid and imports_valid and config_valid:
        print("\n🎉 All validations passed! Project is ready to use.")
        print("\n📝 Next steps:")
        print("  1. Run 'python setup.py' to configure email settings")
        print("  2. Run 'python Desafio-4-RH.py' to execute the HR process")
        return True
    else:
        print("\n⚠️ Some validations failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)