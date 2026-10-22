import numpy as np
from supplement_seasonal_learning_20261020 import fractional_arrays, time_blocks, L, H


def test_fraction_normalizer_and_fixed_evaluation_periods():
    # An extreme excluded old value must not change the suffix's fitted normalizer.
    train=np.arange(800,dtype=np.float32).reshape(400,2)/50
    a=dict(train=train.copy(),val=train[:140].copy(),test=train[:140].copy(),
           mean=np.array([3.,4.]),std=np.array([2.,3.]))
    x,meta=fractional_arrays(a,50)
    a['train'][:200]=1e6
    y,meta2=fractional_arrays(a,50)
    np.testing.assert_allclose(meta['mean'],meta2['mean'])
    np.testing.assert_allclose(meta['std'],meta2['std'])
    for split in ['train','val','test']:np.testing.assert_allclose(x[split],y[split])
    np.testing.assert_allclose(x['train'].mean(axis=0),0,atol=1e-6)
    np.testing.assert_allclose(x['train'].std(axis=0),1,atol=1e-6)
    assert len(x['val'])==140 and len(x['test'])==140


def test_target_blocks_do_not_share_any_target_timestamp():
    n=932;origins=np.arange(L,n-H+1)
    used=[]
    for block in time_blocks(n):
        times=set((origins[block['mask']][:,None]+np.arange(H)).ravel())
        assert times
        for previous in used:assert times.isdisjoint(previous)
        used.append(times)


def test_seasonal_references_never_read_forecast_targets():
    origins=np.arange(168,400-H+1)
    targets=origins[:,None]+np.arange(H)
    for lag in [24,168]:assert np.all(targets-lag < origins[:,None])
