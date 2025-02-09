import xml.etree.ElementTree as ET
from model.bml import BML

class BMLService:

    # Function to deserialize a xml to a BML object
    def deserialize(self, xml_string):
        root = ET.fromstring(xml_string)
        bmle = BML(character=root.attrib['character'], id=root.attrib['id'])
        for child in root:
            if child.tag == 'posture':
                bmle.posture = child.attrib['lexeme']
            elif child.tag == 'gaze':
                bmle.gaze = child.attrib['target']
            elif child.tag == 'face':
                bmle.face = child.attrib['lexeme']
            elif child.tag == 'gesture':
                bmle.gesture = child.attrib['lexeme']
            elif child.tag.endswith('speech'):
                bmle.speech = {
                    'tone': child.attrib['tone'],
                    'speed': child.attrib['speed'],
                    'text': child.find('text').text,
                    'end': child.attrib['end'].lower() == 'true'
                }
        return bmle