# acts-validation


```sh
python -i ~/compare_profiles.py -i itk_gen2_propagation_summary.root itk_detray_gen2_propagation_summary.root -x eta --x-ranges-min -4 --x-ranges-max 4 --x-bin 60 -y nSensitives  -c blue green -t propagation_summary  -m o "*" ^  --x-labels η --x-label-size 16 --y-labels "# sensitive modules / track" -d range --y-label-size 16 -l ACTS detray
```