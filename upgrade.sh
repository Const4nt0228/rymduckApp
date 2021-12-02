fspec=$1
filename="${fspec##*/}"  # get filename
dirname="${fspec%/*}" # get directory/path name

rm ./$fspec

mkdir ./upgrade_cache
chmod -R 755 ./upgrade_cache
cd upgrade_cache
mkdir ./tmp

echo download .$fspec

wget $fspec

echo extract

tar -zxvf $filename -C ./tmp
cd tmp

echo copy

cp -rf * ../../

echo move dir

cd ../../

echo cachedel

rm -Rf ./upgrade_cache

if [ -f "./after_upgrade.sh" ]
then
  chmod -R 755 ./after_upgrade.sh
  ./after_upgrade.sh
  rm -Rf ./after_upgrade.sh
fi

chmod -R 755 ./*.sh
./launch.sh
