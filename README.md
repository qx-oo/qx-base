# qx-base
my django project basic module

### Usage:


### Mac OS:

    brew install gmp
    export "CFLAGS=-I/usr/local/include -L/usr/local/Cellar/gmp/6.2.0/lib"

### Signature Keys

    openssl genrsa -out rsa_pri_key.pem 1024
    openssl rsa -in rsa_pri_key.pem -pubout -out rsa_pub_key.pem