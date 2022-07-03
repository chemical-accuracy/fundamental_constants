YEARS=(2010 2014 2018)
LANGS=("fortran" "c" "python" "matlab" "mathematica")
for year in ${YEARS[@]}  ; do
	for lang in ${LANGS[@]} ; do
		./nist.py -y $year -l $lang
	done
done
