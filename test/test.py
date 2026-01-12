#!/usr/bin/env python3
"""
Test suite for the steganography encoder/decoder
"""

import sys
sys.path.insert(0, '.')

from main import encode, decode

def test_basic_encoding():
    """Test basic lowercase and numbers"""
    carrier = "The quick brown fox jumps over the lazy dog."
    secret = "hello world 123456789"
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected '{secret}', got '{decoded}'"
        print("✓ Basic encoding test passed")
        return True
    except Exception as e:
        print(f"✗ Basic encoding test failed: {e}")
        return False

def test_uppercase_special():
    """Test uppercase and special characters"""
    carrier = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    secret = "HELLO WORLD!@#$%"
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected '{secret}', got '{decoded}'"
        print("✓ Uppercase and special characters test passed")
        return True
    except Exception as e:
        print(f"✗ Uppercase and special characters test failed: {e}")
        return False

def test_all_digits():
    """Test all digits 0-9"""
    carrier = "Testing all digits in the secret message here."
    secret = "0123456789"
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected '{secret}', got '{decoded}'"
        print("✓ All digits test passed")
        return True
    except Exception as e:
        print(f"✗ All digits test failed: {e}")
        return False

def test_mixed_content():
    """Test mixed content with all character sets"""
    carrier = "This is a longer carrier text that can hold more secret information."
    secret = "abc123XYZ!@# test"
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected '{secret}', got '{decoded}'"
        print("✓ Mixed content test passed")
        return True
    except Exception as e:
        print(f"✗ Mixed content test failed: {e}")
        return False

def test_emoji():
    """Test emoji and unicode characters"""
    carrier = "A very long carrier text with many characters to accommodate emoji encoding which requires more space."
    secret = "hello 😀🎉"
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected '{secret}', got '{decoded}'"
        print("✓ Emoji test passed")
        return True
    except Exception as e:
        print(f"✗ Emoji test failed: {e}")
        return False

def test_carrier_too_short():
    """Test that proper error is raised when carrier is too short"""
    carrier = "Short"
    secret = "This is a very long secret message that won't fit"
    
    try:
        encoded = encode(carrier, secret)
        print("✗ Carrier too short test failed: Should have raised ValueError")
        return False
    except ValueError as e:
        if "too short" in str(e).lower():
            print("✓ Carrier too short test passed")
            return True
        else:
            print(f"✗ Carrier too short test failed: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"✗ Carrier too short test failed: Wrong exception type: {e}")
        return False

def test_empty_secret():
    """Test encoding empty secret"""
    carrier = "Carrier text"
    secret = ""
    
    try:
        encoded = encode(carrier, secret)
        decoded = decode(encoded)
        
        assert decoded == secret, f"Expected empty string, got '{decoded}'"
        print("✓ Empty secret test passed")
        return True
    except Exception as e:
        print(f"✗ Empty secret test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 50)
    print("Running Steganography Tests")
    print("=" * 50)
    
    tests = [
        test_basic_encoding,
        test_uppercase_special,
        test_all_digits,
        test_mixed_content,
        test_emoji,
        test_carrier_too_short,
        test_empty_secret,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    return all(results)

if __name__ == "__main__":
    if "--test" in sys.argv or len(sys.argv) == 1:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python test.py [--test]")
        sys.exit(1)
