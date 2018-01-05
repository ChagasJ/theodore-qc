#!/bin/bash

PDIR=`pwd`

echo "theo_test.bash [<module>]"
echo "  available modules: standard, all, openbabel, cclib, adf, noadf"

echo "Starting theo_test.bash"
echo "THEODIR=$THEODIR"

if [ -z "$THEODIR" ]; then
   echo "ERROR: Please set the THEODIR environment variable!"
   exit 1
fi

stddirs="pyrrole.qcadc hexatriene.colmrci fa2.ricc2 pv2p.escf pv2p.qctddft pyridine.ricc2 fa2.col fa2.rassi fa2.rassi-libwfa fa2.terachem tyrosine.ricc2-es2es biphenyl.tddftb"
obdirs="ir_c3n3.qctddft"
cclibdirs="fa2.cclib SnH4-ecp.firefly"
adfdirs="fa2.adf"

if [ $# == 0 ]
then
    rundirs=$stddirs
else
    case "$1" in
    "all") rundirs="$stddirs $obdirs $cclibdirs $adfdirs";;
    "noadf") rundirs="$stddirs $obdirs $cclibdirs";;
    "standard") rundirs="$stddirs";;
    "openbabel") rundirs="$obdirs";;
    "cclib") rundirs="$cclibdirs";;
    "adf") rundirs="$adfdirs";;
    esac
fi

rm -r RUN_THEO_TEST
mkdir RUN_THEO_TEST || exit 1

tchk=0
for dir in $rundirs
do
    echo
    echo "================================================"
    echo
    echo "Starting test $dir ..."
    sdir="$THEODIR/EXAMPLES/$dir"

    rdir="$PDIR/RUN_THEO_TEST/$dir"
    if [ -d $rdir ]
    then
        echo " ERROR:"
        echo "$rdir already exists! Please delete it or run in a different directory."
        exit 5
    fi

    cp -r "$sdir/QC_FILES" $rdir
    cd $rdir

    chk=0
    for ifile in `ls "$sdir/IN_FILES"`
    do
        cp $sdir/IN_FILES/$ifile .

        dtype=`echo $ifile | cut -d '.' -f 1`
        atype=`echo $ifile | cut -d '.' -f 3`
        comm="analyze_$dtype.py -ifile $ifile"
        echo $comm
        $comm > analyze_$atype.out
        lchk=$?
        if [ "$lchk" -ne 0 ]
        then
            echo "  ... failed!"
        fi

        chk=$((chk+lchk))
    done

    echo
    echo "Checking primary output files:"
    for rfile in `ls "$sdir/REF_FILES"`
    do
        echo "  -> $rfile"
        diff -w -I 'TheoDORE\|python-openbabel\|emulation\|wall time' "$sdir/REF_FILES/$rfile" $rfile
        chk=$((chk+$?))
    done

    echo
    if [ -d $sdir/REF_FILES_SEC ]
    then
        echo "Checking secondary output files:"
        echo "  (These may show some numerical inaccuracies)"
        for rfile in `ls "$sdir/REF_FILES_SEC"`
        do
            echo "  -> $rfile"
            diff -q "$sdir/REF_FILES_SEC/$rfile" $rfile
            diff "$sdir/REF_FILES_SEC/$rfile" $rfile >> $PDIR/RUN_THEO_TEST/diff_sec.out
        done
    fi

    echo
    echo " *** Test $dir finished (error code: $chk)."
    tchk=$((tchk+chk))
done
echo
echo "================================================"
echo
echo " *** All tests finished (number of errors: $tchk)"
echo
echo "================================================"

exit $tchk
