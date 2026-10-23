"""
Molecular property extraction using RDKit.
Falls back gracefully if RDKit is unavailable or SMILES is invalid.
"""

from typing import Optional, Dict, Any

import logging

logger = logging.getLogger(__name__)

try:

    from rdkit import Chem

    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors

    RDKIT_AVAILABLE = True

except ImportError:

    RDKIT_AVAILABLE = False

    logger.warning("RDKit not installed – molecular properties will be limited")

def smiles_from_name(name: str) -> Optional[str]:

    """
    Very small local lookup for common drugs.
    In production replace with PubChem / ChEMBL API.
    """

    name_lower = name.strip().lower()

    LOOKUP = {

        "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",

        "paracetamol": "CC(=O)NC1=CC=C(O)C=C1",

        "acetaminophen": "CC(=O)NC1=CC=C(O)C=C1",

        "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",

        "metformin": "CN(C)C(=N)NC(=N)N",

        "amlodipine": "CCOC(=O)C1=C(COCCN)NC(=C(C1C2=CC=CC=C2Cl)C(=O)OC)C",

        "atorvastatin": "CC(C)C1=C(C(=C(N1CC[C@H](C[C@H](CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",

        "omeprazole": "CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC",

        "losartan": "CCCCC1=NC(=C(N1CC2=CC=C(C=C2)C3=CC=CC=C3C4=NNN=N4)CO)Cl",

        "warfarin": "CC(=O)CC(C1=CC=CC=C1)C2=C(C3=CC=CC=C3OC2=O)O",

        "digoxin": "C[C@H]1O[C@@H](O[C@H]2C[C@@H](O[C@@H]3C[C@@H](O[C@H]4CC[C@]5(C)[C@H]6C[C@H](O)[C@]7(C)[C@H](CC[C@]7(O)C6=CC(=O)C5C4)C4=CC(=O)OC4)C[C@]3(O)C)C[C@]2(O)C)C[C@H](O)[C@H]1O",

    }

    return LOOKUP.get(name_lower)

def extract_molecular_properties(identifier: str) -> Dict[str, Any]:

    """
    identifier can be a drug name or a SMILES string.
    Returns a dict compatible with MolecularProperties schema.
    """

    result = {

        "molecular_weight": None,

        "logp": None,

        "tpsa": None,

        "hbd": None,

        "hba": None,

        "smiles": None,

        "is_valid_molecule": False,

    }

    if not RDKIT_AVAILABLE:

        return result

    smiles = identifier.strip()

                                                                           

    if not any(c in smiles for c in ["=", "#", "(", ")", "[", "]"]) and " " not in smiles:

        looked_up = smiles_from_name(smiles)

        if looked_up:

            smiles = looked_up

        else:

                                                      

            pass

    try:

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:

            return result

        result["smiles"] = Chem.MolToSmiles(mol)

        result["molecular_weight"] = round(Descriptors.MolWt(mol), 2)

        result["logp"] = round(Crippen.MolLogP(mol), 2)

        result["tpsa"] = round(Descriptors.TPSA(mol), 2)

        result["hbd"] = rdMolDescriptors.CalcNumHBD(mol)

        result["hba"] = rdMolDescriptors.CalcNumHBA(mol)

        result["is_valid_molecule"] = True

    except Exception as e:

        logger.warning(f"RDKit failed for {identifier}: {e}")

    return result

def get_basic_drug_knowledge(name: str) -> Dict[str, Any]:

    """
    Tiny static knowledge base for MVP.
    In production: DrugBank / ChEMBL / local DB.
    """

    name_lower = name.strip().lower()

    KB = {

        "ibuprofen": {

            "targets": ["COX-1", "COX-2"],

            "metabolism": ["CYP2C9", "oxidation"],

            "cyp_enzymes": ["CYP2C9"],

            "therapeutic_window": "10-50 mg/L (approx)",

        },

        "paracetamol": {

            "targets": ["COX (central)"],

            "metabolism": ["UGT", "CYP2E1", "SULT"],

            "cyp_enzymes": ["CYP2E1"],

            "therapeutic_window": "10-20 mg/L",

        },

        "acetaminophen": {

            "targets": ["COX (central)"],

            "metabolism": ["UGT", "CYP2E1", "SULT"],

            "cyp_enzymes": ["CYP2E1"],

            "therapeutic_window": "10-20 mg/L",

        },

        "metformin": {

            "targets": ["AMPK", "mitochondrial complex I"],

            "metabolism": ["not metabolized – renal excretion"],

            "cyp_enzymes": [],

            "therapeutic_window": "1-4 mg/L",

        },

        "amlodipine": {

            "targets": ["L-type calcium channel"],

            "metabolism": ["CYP3A4"],

            "cyp_enzymes": ["CYP3A4"],

            "therapeutic_window": "5-15 ng/mL",

        },

        "warfarin": {

            "targets": ["VKORC1"],

            "metabolism": ["CYP2C9", "CYP3A4", "CYP1A2"],

            "cyp_enzymes": ["CYP2C9", "CYP3A4", "CYP1A2"],

            "therapeutic_window": "INR guided",

        },

    }

    return KB.get(name_lower, {

        "targets": [],

        "metabolism": ["unknown – limited data"],

        "cyp_enzymes": [],

        "therapeutic_window": None,

    })

