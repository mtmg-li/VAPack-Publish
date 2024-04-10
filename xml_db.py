import xml.etree.ElementTree as ET
from datetime import datetime
from numpy import random as nprand
from hashlib import sha256
from pathlib import Path

def arbitrary_hash(n=12):
    # Get time and random number to update hash
    time = datetime.now()
    rnum = nprand.randint(0,9999)
    # Make the hash
    h = sha256()
    h.update(f'{time}-{rnum}'.encode())
    h.digest()
    # Only return up to first n characters
    return h.hexdigest()[:n]

class Calculation:
    """Calculation metadata class"""
    
    def __init__(self, location:Path, id:str=None, description:str=None, \
                 created:str=None, status:str=None, parent:str=None) -> None:
        # Set the standard internal variables, none of which should be callable
        self.id = arbitrary_hash() if id is None else str(id)
        self._check_id()
        try:
            self.location = Path(location)
        except:
            raise RuntimeError("Could not parse location for C-{self.id}: {location}")
            
        self.description = description
        try:
            self.created = datetime.fromisoformat(created) if created is not(None) \
                           else datetime.now().replace(microsecond=0)
            self.created = self.created.isoformat()
        except ValueError:
            raise RuntimeError(f"Could not parse datetime for C-{self.id}: {created}")
        self.status = str(status) if parent is not(None) else None
        self.parent = str(parent) if parent is not(None) else None
        # Make sure to update the member _xml_root variable
        self._update_xml()

    def _check_id(self) -> None:
        banned_characters = ['/','\\','*']
        instances = [key for key in banned_characters if key in self.id]
        if len(instances) > 0:
            raise RuntimeError("ID cannot contain: \'{}\'".format('\', \''.join(instances)))

    def _update_xml(self) -> None:
        # Update root
        root_attrib = {'id': self.id, 'location': str(self.location)}
        self._xml_root = ET.Element('calculation', root_attrib)
        # Pythonically update the xml element tree with all members variables
        # that don't start with _
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) \
                   and not attr.startswith("_") and not attr in ['id','location']]
        for member in members:
            xml_attr = f"_xml_{member}"
            self.__setattr__(xml_attr, ET.SubElement(self._xml_root, member))
            xml_attr = self.__getattribute__(xml_attr)
            if self.__getattribute__(member) is not(None):
                xml_attr.text = str(self.__getattribute__(member))
        # Prettify with indentation
        ET.indent(self._xml_root)

    def to_xml(self) -> ET.Element:
        """Export an XML element containing calculation data"""
        self._update_xml()
        return self._xml_root
        
    def to_string_xml(self) -> str:
        """Return a string of the prettified xml"""
        self._update_xml()
        return ET.tostring(self._xml_root, encoding='unicode')

def from_xml(xml:str) -> Calculation:
    # TODO: Implement from_xml
    pass