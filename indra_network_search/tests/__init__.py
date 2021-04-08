from depmap_analysis.network_functions.net_functions import _weight_from_belief


__all__ = ['nodes', 'edge_data']

wm = _weight_from_belief


nodes = {'BRCA1': {'ns': 'HGNC', 'id': '1100'},
         'BRCA2': {'ns': 'HGNC', 'id': '1101'},
         'CHEK1': {'ns': 'HGNC', 'id': '1925'},
         'AR': {'ns': 'HGNC', 'id': '644'},               # A
         'testosterone': {'ns': 'CHEBI', 'id': '17347'},  # B
         'NR2C2': {'ns': 'HGNC', 'id': '7972'},           # C
         'MBD2': {'ns': 'HGNC', 'id': '6917'},            # D
         'PATZ1': {'ns': 'HGNC', 'id': '13071'},          # E
         'HDAC3': {'ns': 'HGNC', 'id': '4854'},           # F
         'H2AZ1': {'ns': 'HGNC', 'id': '4741'},           # G (unused in edges)
         'NCOA': {'ns': 'FPLX', 'id': 'NCOA'}}            # H (unused in edges)

edge_data = {
        ('BRCA1', 'AR'): {'belief': 0.999999,
                          'weight': wm(0.999999),
                          'statements': [{
            'stmt_hash': 5603789525715921, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds AR.'}]
        },
        ('BRCA1', 'testosterone'): {'belief': 0.99999,
                                    'weight': wm(0.99999),
                                    'statements': [{
            'stmt_hash': 5603789525715922, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds testosterone.'}]
        },
        ('BRCA1', 'NR2C2'): {'belief': 0.9999,
                             'weight': wm(0.9999),
                             'statements': [{
            'stmt_hash': 5603789525715923, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds NR2C2.'}]
        },
        ('BRCA1', 'MBD2'): {'belief': 0.999,
                            'weight': wm(0.999),
                            'statements': [{
            'stmt_hash': 5603789525715924, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds MBD2.'}]
        },
        ('BRCA1', 'PATZ1'): {'belief': 0.99,
                             'weight': wm(0.99),
                             'statements': [{
            'stmt_hash': 5603789525715924, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds PATZ1.'}]
        },
        ('AR', 'CHEK1'): {'belief': 0.9, 'weight': wm(0.9), 'statements': [
            {'stmt_hash': 915990, 'stmt_type': 'Activation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 activates BRCA2.'}]
        },
        ('testosterone', 'CHEK1'): {'belief': 0.9, 'weight': wm(0.9),
                                    'statements': [
            {'stmt_hash': 915991, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('NR2C2', 'CHEK1'): {'belief': 0.9, 'weight': wm(0.9), 'statements': [
            {'stmt_hash': 915992, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('MBD2', 'CHEK1'): {'belief': 0.9, 'weight': wm(0.9), 'statements': [
            {'stmt_hash': 560370, 'stmt_type': 'Complex',
             'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
             'residue': None, 'weight': 2, 'curated': False, 'position': None,
             'english': 'MBD2 binds CHEK1.'}]
        },
        ('PATZ1', 'CHEK1'): {'belief': 0.9, 'weight': wm(0.9), 'statements': [
            {'stmt_hash': 560370, 'stmt_type': 'Complex',
             'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
             'residue': None, 'weight': 2, 'curated': False, 'position': None,
             'english': 'PATZ1 binds HDAC3.'}]
        },
        ('CHEK1', 'BRCA2'): {'belief': 0.98, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915993, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.79, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('CHEK1', 'NCOA'): {'belief': 0.7, 'weight': wm(0.6), 'statements': [
            {'stmt_hash': 915994, 'stmt_type': 'Farnesylation',
             'evidence_count': 1, 'belief': 0.7, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 farnesylates NCOA.'}]
        },
        ('NCOA', 'BRCA2'): {'belief': 0.7, 'weight': wm(0.6), 'statements': [
            {'stmt_hash': 915995, 'stmt_type': 'Acetylation',
             'evidence_count': 1, 'belief': 0.7, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'NCOA acetylates BRCA2.'}]
        },
        ('BRCA2', 'BRCA1'): {'belief': 0.98, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': -976543, 'stmt_type': 'Deactivation',
             'evidence_count': 1, 'belief': 0.79, 'source_counts': {'pc': 1},
             'residue': None, 'weight': 0.23572233352106983, 'curated': True,
             'position': None, 'english': 'CHEK1 deactivates BRCA2.'}]
        },
}
