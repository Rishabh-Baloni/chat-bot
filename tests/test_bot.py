import sys
import os
import json
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import determine_next_stage

class TestBot(unittest.TestCase):
    def test_treatment_request(self):
        # Test if "tell me the treatment" triggers conclusion
        stage = determine_next_stage("symptom_gathering", "now tell me the treatment", "User: hi\nAssistant: hi")
        self.assertEqual(stage, "conclusion", "Should switch to conclusion on treatment request")

    def test_elbow_knowledge(self):
        # Test if elbow pain knowledge exists
        with open('knowledge/core_knowledge.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        found = False
        for entry in data:
            if "Fall-Related Elbow Pain and Numbness" in entry['topic']:
                found = True
                break
        self.assertTrue(found, "Elbow pain knowledge missing")

if __name__ == '__main__':
    unittest.main()