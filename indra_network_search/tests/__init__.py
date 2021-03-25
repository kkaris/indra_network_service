nodes = {'BRCA1': {'ns': 'HGNC', 'id': '1100'},
         'BRCA2': {'ns': 'HGNC', 'id': '1101'},
         'CHEK1': {'ns': 'HGNC', 'id': '1925'},
         'A': {'ns': 'ns', 'id': '0'},
         'B': {'ns': 'ns', 'id': '1'},
         'C': {'ns': 'ns', 'id': '2'},
         'D': {'ns': 'ns', 'id': '3'},
         'E': {'ns': 'ns', 'id': '4'}}

edge_data = {
        ('BRCA1', 'A'): {'belief': 1, 'weight': 2, 'statements': [{
            'stmt_hash': 5603789525715921, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds A.'}]
        },
        ('BRCA1', 'B'): {'belief': 1, 'weight': 2, 'statements': [{
            'stmt_hash': 5603789525715922, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds B.'}]
        },
        ('BRCA1', 'C'): {'belief': 1, 'weight': 2, 'statements': [{
            'stmt_hash': 5603789525715923, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds C.'}]
        },
        ('BRCA1', 'D'): {'belief': 1, 'weight': 2, 'statements': [{
            'stmt_hash': 5603789525715924, 'stmt_type': 'Complex',
            'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
            'residue': None, 'weight': 2, 'curated': False, 'position': None,
            'english': 'BRCA1 binds D.'}]
        },
        ('A', 'CHEK1'): {'belief': 0.99, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915990, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('B', 'CHEK1'): {'belief': 0.99, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915991, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('C', 'CHEK1'): {'belief': 0.99, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915992, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.99, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('D', 'E'): {'belief': 1, 'weight': 2, 'statements': [
            {'stmt_hash': 560370, 'stmt_type': 'Complex',
             'evidence_count': 1, 'belief': 1, 'source_counts': {'sparser': 1},
             'residue': None, 'weight': 2, 'curated': False, 'position': None,
             'english': 'BRCA1 binds E.'}]
        },
        ('CHEK1', 'BRCA2'): {'belief': 0.98, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915993, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.79, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
        ('E', 'BRCA2'): {'belief': 0.98, 'weight': 4.1e-05, 'statements': [
            {'stmt_hash': 915994, 'stmt_type': 'Phosphorylation',
             'evidence_count': 1, 'belief': 0.79, 'source_counts': {'pc': 1},
             'residue': 'T', 'weight': 0.23572233352106983, 'curated': True,
             'position': '3387', 'english': 'CHEK1 phosphorylates BRCA2.'}]
        },
}
