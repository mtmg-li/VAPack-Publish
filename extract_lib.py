from xml.etree import ElementTree as ET
import numpy as np

def get_xml_root(file:str) -> ET.Element:
    return ET.parse(file).getroot()

def inline_value_string(head:str, fields:dict):
    '''
    Return a formatted string of the given dictionary, ready for Obsidian.
    '''
    ss = f'### {head}\n\n'
    for field, value in fields.items():
        if not(type(value[0]) in [tuple, list, np.array]):
            ss += f'[ {field}:: {value[0]} ] {value[1]}\n'
        else:
            ss += f'[ {field}:: ' + ', '.join([str(j) for j in value[0]]) + f' ] {value[1]}\n'
    return ss


def get_lattices(root:ET.Element) -> dict:
    '''
    Return a dictionary containing the initial and final lattice parameters
    '''
    for s in root.findall('structure'):
        if s.get('name') == 'initialpos':
            minit = np.vstack( [ np.array(v.text.split()) for v in s.find('crystal').find('varray') ] )

        if s.get('name') == 'finalpos':
            mfinal = np.vstack( [ np.array(v.text.split()) for v in s.find('crystal').find('varray') ] )

    vinit = [np.linalg.norm(v) for v in minit]
    vfinal = [np.linalg.norm(v) for v in mfinal]
    
    lattice_dict = {'a_i' : [vinit, 'Å'], 'a_f' : [vfinal, 'Å']}
    return lattice_dict


def get_ions(root:ET.Element) -> dict:
    '''
    Return a count of the ions in the system
    '''
    n = int(root.find('atominfo').find('atoms').text)
    return {'ions' : [n,'']}


def get_energies(root:ET.Element) -> dict:
    '''
    Return a dictionary of the various energies
    '''
    energies = root.find('calculation').find('energy')
    en_free, en_wo_entropy, en_0 = [float(e.text) for e in energies]

    energy_dict = {'en_fr' : [en_free, 'eV'],
                   'en_we' : [en_wo_entropy, 'eV'],
                   'en_0' : [en_0, 'eV'],
                   'en_we/atom' : [en_wo_entropy/get_ions(root)['ions'][0], 'eV/ion']}
    return energy_dict