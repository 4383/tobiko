====================
Enabling in Devstack
====================

**WARNING**: the stack.sh script must be run in a disposable VM that is not
being created automatically, see the README.md file in the "devstack"
repository.  See contrib/vagrant to create a vagrant VM.

1. Download DevStack::

    git clone https://opendev.org/openstack/devstack.git
    cd devstack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin tobiko https://opendev.org/x/tobiko

3. Tobiko require Heat to be enabled, so heat should be also enabled::

   [[local|localrc]]
   enable_plugin heat https://opendev.org/openstack/heat


3. Run ``stack.sh``
