from pathlib import Path
from hashlib import sha256
import importlib.metadata
from datetime import datetime, timezone
import json
import sys

import numpy as np
import pandas as pd
import tables

sys.stdout.reconfigure(encoding='utf-8')
root = Path(__file__).resolve().parents[2]
qa = Path(__file__).resolve().parent
records = []
for path in (root/'abilene_forecasting/data/raw/tszoo/databases').glob('*/*1_hour.h5'):
    with tables.open_file(path, 'r') as f:
        print(path.name)
        print('root attributes:', {k: str(f.root._v_attrs[k]) for k in f.root._v_attrs._f_list()})
        for node_path in ['/times/times_1_hour', '/backbone_network/agg_1_hour', '/backbone_network/id_ranges_agg_1_hour', '/backbone_network/identifiers']:
            node = f.get_node(node_path)
            print(node_path, node.dtype, 'first', node[:2], 'last', node[-2:])
        time_node = f.root.times.times_1_hour
        time_values = time_node.read()
        assert np.all(np.diff(time_values['time']) == 3600)
        dataset = path.parent.name.lower()
        feature = 'matrix_avg_realOD' if dataset == 'abilene' else 'matrix_avg_bandwidth_kbps'
        aggregation = f.root.backbone_network.agg_1_hour.read()
        raw_matrix = f.get_node('/backbone_network/'+feature).read()
        reconstructed = np.zeros((len(time_values), raw_matrix.shape[1] * raw_matrix.shape[2]), dtype=np.float64)
        reconstructed[aggregation['id_time']] = raw_matrix[aggregation['id_'+feature]].reshape(len(aggregation), -1)
        reconstructed = np.maximum(np.nan_to_num(reconstructed, nan=0, posinf=0, neginf=0), 0)
        logged = np.log1p(reconstructed)
        train_end = int(len(logged)*.6)
        val_end = int(len(logged)*.8)
        mask = logged[:train_end].std(axis=0) > 1e-8
        logged = logged[:, mask]
        average = logged[:train_end].mean(axis=0)
        scale = logged[:train_end].std(axis=0)
        scale[scale < 1e-8] = 1
        normalized = (logged-average)/scale
        processed = root/'abilene_forecasting/data/processed'/f'{dataset}_1hour.npz'
        with np.load(processed) as saved:
            assert np.array_equal(mask.nonzero()[0], saved['active_indices'])
            for name, values in [('train',normalized[:train_end]),('val',normalized[train_end:val_end]),('test',normalized[val_end:])]:
                assert np.array_equal(values.astype(np.float32), saved[name]), (dataset,name)
        records.append({'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
                        'times_dtype': str(time_values.dtype), 'first_time_row': str(time_values[0]),
                        'last_time_row': str(time_values[-1]), 'time_count': len(time_values),
                        'aggregation_count': len(f.root.backbone_network.agg_1_hour),
                        'first_utc': datetime.fromtimestamp(int(time_values['time'][0]),timezone.utc).isoformat(),
                        'last_utc': datetime.fromtimestamp(int(time_values['time'][-1]),timezone.utc).isoformat(),
                        'time_values': time_values.tolist(),
                        'processed_path': str(processed), 'processed_sha256': sha256(processed.read_bytes()).hexdigest(),
                        'preprocessing_reconstructed_and_matches_saved_data_exactly': True})
result = {'cesnet_tszoo_version': importlib.metadata.version('cesnet-tszoo'), 'data': records}
(qa/'data_metadata_raw.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
