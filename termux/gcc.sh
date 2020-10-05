#https://android.stackexchange.com/questions/182130/use-gcc-compiler-in-termux


#I created termux repo with gcc 10.2.0, there how to install https://cctools.info/index.php/Termux_repository_with_cctools_packages_(gcc_with_fortran_support_etc)

#Add cctools packages public key:

wget -O - https://cctools.info/public.key | apt-key add -

#Create a new repository list:

echo "deb https://cctools.info termux cctools" > $PREFIX/etc/apt/sources.list.d/cctools.list

#Update packages lists:

apt update

#Install the package gcc-cctools(it will install binutils-cctools automatically):

apt install gcc-cctools

#Install the NDK package for your android architecture, use the latest one, for example for aarch64:

apt install ndk-sysroot-cctools-api-26-aarch64

#To show all ndk sysroots for aarch64:

apt search ndk-sysroot-cctools | grep aarch64

#Add directory with new compilers to PATH:

export PATH=$PREFIX/../cctools-toolchain/bin:$PATH

#Check it:

gcc -v
