blach=$($USERCONFIG_ROOT/blach/find_blach.py)

echo -e "${Blue}USING BLACH FROM $blach${None}"
echo $blach > $state_run_dir/blach_path
(cd $blach && git -c safe.directory=* rev-parse --verify HEAD) > $state_run_dir/blach_commit
