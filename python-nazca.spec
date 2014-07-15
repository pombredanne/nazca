# for el5, force use of python2.6
%if 0%{?el5}
%define python python26
%define __python /usr/bin/python2.6
%else
%define python python
%define __python /usr/bin/python
%endif
%{!?_python_sitelib: %define _python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           %{python}-nazca
Version:        0.6.1
Release:        logilab.1%{?dist}
Summary:        Python library for data alignment

Group:          Development/Libraries
License:        LGPL
Source0:        nazca-%{version}.tar.gz
BuildArch:      noarch
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:  %{python}
Requires:       %{python}
Requires:       scipy
Requires:       %{python}-sklearn


%description
Python library for data alignment

%prep
%setup -q -n nazca-%{version}


%build
%{__python} setup.py build
%if 0%{?el5}
# change the python version in shebangs
find . -name '*.py' -type f -print0 |  xargs -0 sed -i '1,3s;^#!.*python.*$;#! /usr/bin/python2.6;'
%endif


%install
rm -rf $RPM_BUILD_ROOT
NO_SETUPTOOLS=1 %{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
/*