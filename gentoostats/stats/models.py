from django.db import models
from django.core.validators import RegexValidator, URLValidator, validate_email

# validators:
# cpatom_validator = RegexValidator("^\w+-\w+/[\w-]+$")
# url_validator    = URLValidator()

# NOTE: This may look counter-intuitive, but I have not used camel case here in
#       the name of consistency.

class Host(models.Model):
    uuid       = models.CharField(max_length=16, primary_key=True)
    secret_key = models.CharField("secret key (needed to upload stats)", max_length=64)

    # should users be allowed to delete their profile + submissions? should
    # these be actually deleted from the db?
    deleted = models.BooleanField(default=False, db_index=True)

    # TODO: what if the user wants to change his secret_key?
    # Should we support this?

    # a small optimisation:
    # latest_submission = TODO

    def __unicode__(self):
        return self.uuid

    def get_absolute_url():
        # TODO
        pass

class Submission(models.Model):
    host     = models.ForeignKey(Host)
    ip_addr  = models.GenericIPAddressField()
    fwd_addr = models.GenericIPAddressField(blank=True) # X-Forwarded-For
    datetime = models.DateTimeField(auto_now_add=True)
    protocol = models.IntegerField()

    # This is used for testing ATM.
    deleted = models.BooleanField(default=False, db_index=True)

    # The email can change between submissions, so let's store it here.
    # Also, let's 'accept' invalid email addresses for the time being.
    email    = models.EmailField(blank=True, max_length=256)
     #email    = models.CharField(blank=True, max_length=256)

    # ACCEPT_KEYWORDS (Example: "~amd64")
    arch     = models.CharField(blank=True, max_length=32)

    # arch-vendor-OS-libc (Example: "x86_64-pc-linux-gnu")
    chost    = models.CharField(blank=True, max_length=64)

    # Cross-compiling variables (build/target CHOSTs):
    cbuild   = models.CharField(blank=True, max_length=64)
    ctarget  = models.CharField(blank=True, max_length=64)

    # Platform (Example: "Linux-3.2.1-gentoo-r2-x86_64-Intel-R-_Core-TM-_i3_CPU_M_330_@_2.13GHz-with-gentoo-2.0.3")
    platform = models.CharField(blank=True, max_length=128) # don't normalise this

    # Active Gentoo profile:
    profile  = models.CharField(blank=True, max_length=128)

    # System locale (Example: "en_US.utf8")
    lang     = models.ManyToManyField('Lang', blank=True, related_name='submission')

    # Last sync time:
    lastsync = models.DateTimeField(blank=True)

    # make.conf:
    makeconf = models.TextField(blank=True)

    # cc flags, c++ flags, ld flags, cpp flags, fortran flags:
    cflags   = models.CharField(blank=True, max_length=128)
    cxxflags = models.CharField(blank=True, max_length=128)
    ldflags  = models.CharField(blank=True, max_length=128)
    cppflags = models.CharField(blank=True, max_length=128)
    fflags   = models.CharField(blank=True, max_length=128)

    # Portage features (enabled in make.conf):
    features = models.ManyToManyField('Feature', blank=True, related_name='submissions')

    # make.conf example: SYNC="rsync://rsync.gentoo.org/gentoo-portage"
    sync = models.ManyToManyField('SyncServer', blank=True, related_name='submissions')

    # make.conf example: GENTOO_MIRRORS="http://gentoo.osuosl.org/"
    mirrors = models.ManyToManyField('MirrorServer', blank=True, related_name='submissions')

    globaluse      = models.ManyToManyField('UseFlag', blank=True, related_name='submissions')
    globalkeywords = models.ManyToManyField('Keyword', blank=True, related_name='submissions')

    installedAtoms = models.ManyToManyField('Atom', blank=True, related_name='submissionsInstalled', through='Installation')
    selectedAtoms  = models.ManyToManyField('Atom', blank=True, related_name='submissionsSelected')

    # misc. make.conf variables:
    makeopts      = models.CharField(blank=True, max_length=128)
    emergeopts    = models.CharField(blank=True, max_length=256)
    syncopts      = models.CharField(blank=True, max_length=256)
    acceptlicense = models.CharField(blank=True, max_length=256)

    def __unicode__(self):
        return "Submission from %s made at %s" % (self.host, self.datetime)

class CPAtom(models.Model):
    """
    Atom that only defines a category plus a package name.
    """

    cat = models.CharField(max_length=32)
    pkg = models.CharField(max_length=128)

    class Meta:
        unique_together = ('cat', 'pkg')

    def __unicode__(self):
        return "CPAtom(%s/%s)" % (cat, pkg)

class Atom(models.Model):
    """
    (repo, category, package, version/slot) as a string (only CP is mandatory)
    """

    atom = models.CharField(primary_key=True, max_length=128)

    # instead of calculating CP every time, normalise it:
    cp = models.ForeignKey(CPAtom, related_name='+')

    def calculateCP(self):
        return "TODO"

    def __unicode__(self):
        return self.atom

class AtomSet(models.Model):
    name  = models.CharField(max_length=128)
    owner = models.ForeignKey('Submission')

    atoms   = models.ManyToManyField('Atom', related_name='parentset')
    subsets = models.ManyToManyField('self', symmetrical=False, related_name='parentset')

    class Meta():
        unique_together = ('name', 'owner')

    # TODO:
    # def __unicode__(self):
    #     return "AtomSet '%s' with '%s' atoms owned by '%s'" % (name, atoms, owner)

class UseFlag(models.Model):
    """
    A USE flag.
    """

    name    = models.CharField(primary_key=True, max_length=64)
    addedon = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class Installation(models.Model):
    """
    Join table containing deta about installed packages on hosts.
    """

    atom       = models.ForeignKey(Atom)
    submission = models.ForeignKey(Submission)

    datetimebuilt = models.DateTimeField()
    duration      = models.TimeField()
    size          = models.IntegerField()

    # enabled and disabled use flags (should be disjoint):
    # TODO: useplus <intersection> useminus should == []
    useplus  = models.ManyToManyField(UseFlag, blank=True, related_name='installationPlus')
    useminus = models.ManyToManyField(UseFlag, blank=True, related_name='installationMinus')
    useunset = models.ManyToManyField(UseFlag, blank=True, related_name='installationUnset')

    # keyword used:
    keyword = models.ForeignKey('Keyword')

    # TODO:
    # def __unicode__(self):
    #     return "Installation: cpv '%s' installed at '%s' with '%s' use flags." % (atom, datetime, useflags)

class Feature(models.Model):
    """
    A Portage FEATURE.
    """

    name    = models.CharField(primary_key=True, max_length=64)
    addedon = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class MirrorServer(models.Model):
    url = models.URLField(primary_key=True, max_length=256)

    def __unicode__(self):
        return self.url

class SyncServer(models.Model):
    url = models.URLField(primary_key=True, max_length=256)

    def __unicode__(self):
        return self.url

class Keyword(models.Model):
    name    = models.CharField(primary_key=True, max_length=128)
    addedon = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class Lang(models.Model):
    name = models.CharField(primary_key=True, max_length=32)

    def __unicode__(self):
        return self.name

# FIXME
# class Repository(models.Model):
#     name = models.CharField(max_length=64)
#     url  = models.CharField(max_length=128)
#
#     class Meta:
#         unique_together = (name, url)
#
#     def __unicode__(self):
#         return self.name
