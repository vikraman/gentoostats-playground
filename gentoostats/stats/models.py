from django.db import models
from django.core.validators import RegexValidator, URLValidator, validate_email

from portage.dep import Atom

# I have tried being consistent with the names defined here:
# http://devmanual.gentoo.org/ebuild-writing/variables/index.html
#
# Atom syntax: operator cat / package_name - version - revision star_operator : slot :: repo [use_flags]
# Examples:    =sys-devel/gcc-4.6.1-r1:4.6::toolchain[cxx(-)]
#              =www-client/google-chrome-18*

DEFAULT_REPO_NAME = 'gentoo'

# 'virtual' match idea taken from euscan. Thanks, fox!
category_validator = RegexValidator('^(?:\w+-\w+)|virtual$')
class Category(models.Model):
    name = models.CharField( primary_key = True
                           , max_length  = 32
                           , validators  = [category_validator]
    )

    @models.permalink
    def get_absolute_url(self):
        return ('category_details_url', (), {'category': self.name})

    def __unicode__(self):
        return self.name

package_name_validator = RegexValidator('^\S+$')
class PackageName(models.Model):
    name = models.CharField( primary_key = True
                           , max_length  = 64
                           , validators  = [package_name_validator]
    )

    def __unicode__(self):
        return self.name

class Repository(models.Model):
    name = models.CharField(max_length=64, db_index=True)
    url  = models.CharField(max_length=256, db_index=True, blank=True)

    # method   = models.CharField(max_length=32)  # e.g. "git"
    # priority = models.IntegerField()            # e.g. 50
    # quality  = models.CharField(max_length=32)  # e.g. "experimental"
    # status   = models.CharField(max_length=32)  # e.g. "official"

    # description
    # owner
    # feed

    class Meta:
        unique_together = ('name', 'url')

    def get_absolute_url(self):
        return "TODO"

    def __unicode__(self):
        return self.name

version_validator  = RegexValidator('^\S+$')
revision_validator = RegexValidator('^r\d+$')
slot_validator     = RegexValidator('^\S+$')

def atom_validator(atom):
    try:
        Atom(atom)
    except InvalidAtom:
        raise ValidationError('%s is not a valid atom' % (atom))
    except:
        # Is there a better way to handle this?
        raise

class Package(models.Model):
    """
    (category, package_name, version, revision, slot, repo)

    Slotting info: http://devmanual.gentoo.org/general-concepts/slotting/index.html
    """

    category     = models.ForeignKey(Category, related_name='+')
    package_name = models.ForeignKey(PackageName, related_name='+')

    version      = models.CharField(max_length=16, validators=[version_validator])
    revision     = models.CharField(max_length=16, blank=True, validators=[revision_validator])
    slot         = models.CharField(max_length=32, blank=True, validators=[slot_validator])
    repository   = models.ForeignKey(Repository, related_name='+')

    class Meta:
        unique_together = ( 'category'
                          , 'package_name'
                          , 'version'
                          , 'revision'
                          , 'slot'
                          , 'repository'
        )

    def __unicode__(self):
        revision   = "-%s" % (self.revision) if self.revision else ''
        slot       = ":%s" % (self.slot) if self.slot else ''
        repository = "::%s" % (self.repository) if self.repo != DEFAULT_REPO_NAME else ''

        return "%s/%s-%s%s%s%s" % ( self.category
                                  , self.package_name
                                  , self.version
                                  , revision
                                  , slot
                                  , repository
        )
    def __unicode__(self):
        return self.full_atom

class Atom(Package):
    """
    Package + operator + possibly postfix operator (*).
    """

    # TODO: operator handling needs more work.

    # '~', '=', '>', '<', '=*', '>=', or '<='
    ATOM_OPERATORS = (
        ('',   'None'),
        ('~',  'Tilde'),
        ('=',  'Equals'),
        ('>',  'GT'),
        ('<',  'LT'),
        ('=*', 'Equals Star'),
        ('>=', 'GE'),
        ('<=', 'LE'),
    )

    ATOM_OPERATORS_POSTFIX = (
        ('',  'None'),
        ('*', 'Star'),
    )

    # TODO: normalise this when everything is properly implemented.
    full_atom = models.CharField(primary_key=True, max_length=64, validators=[atom_validator])
    package   = models.ForeignKey(Package, related_name='atoms')

    # operator         = models.CharField(max_length=2, choices=ATOM_OPERATORS, default='')
    # operator_postfix = models.CharField(max_length=1, choices=ATOM_OPERATORS_POSTFIX, default='')

    def __unicode__(self):
        return self.full_atom

use_flag_validator = RegexValidator('^\S+$')
class UseFlag(models.Model):
    """
    A USE flag.
    """

    name     = models.CharField(primary_key=True, max_length=64, validators=[use_flag_validator])
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

lang_validator = RegexValidator('^\S+$') # TODO
class Lang(models.Model):
    name = models.CharField(primary_key=True, max_length=32, validators=[lang_validator])

    def __unicode__(self):
        return self.name

# UUID format: 8-4-4-4-12 groups of hex.
uuid_validator = RegexValidator('^[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}$')
class Host(models.Model):
    """
    A computer, identified by 32 hexadecimal digits (with hyphens, case
    insensitive).

    UUID Info: http://en.wikipedia.org/wiki/Universally_unique_identifier
               http://tools.ietf.org/html/rfc4122
    """

    id = models.CharField(primary_key=True, max_length=36, validators=[uuid_validator])

    # TODO: prevent accidental overwritting of self.uuid
    # @property
    # def uuid(self):
    #     return self.id

    # This is the 'password' required to upload stats for this host.
    upload_key = models.CharField("upload key (needed to upload stats)", max_length=64)
    # TODO: What if the user wants to change his upload_key?
    # Should we support this at all?

    deleted = models.BooleanField(default=False, db_index=True)
    # TODO: Should users be allowed to delete their profile + submissions?
    # should these be actually deleted from the db?
    # Should old data get removed from the db?

    # A small optimisation:
    # latest_submission = models.ForeignKey('Submission', related_name='+')

    @property
    def latest_submission(self):
        # All hosts must have at least 1 submission.
        return "TODO"

    @models.permalink
    def get_absolute_url(self):
        return ('host_details_url', (), {'id': self.id})

    def __unicode__(self):
        return self.id

feature_validator = RegexValidator('^\S+$')
class Feature(models.Model):
    """
    A Portage FEATURE.
    """

    name     = models.CharField(primary_key=True, max_length=64, validators=[feature_validator])
    added_on = models.DateTimeField(auto_now_add=True)

    @models.permalink
    def get_absolute_url(self):
        # TODO
        return ('feature_details_url', (), {'feature': self.name})

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

# TODO: add validator
class Keyword(models.Model):
    name     = models.CharField(primary_key=True, max_length=128)
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class Installation(models.Model):
    """
    Package installations on hosts.
    """

    package    = models.ForeignKey(Package)
    submission = models.ForeignKey('Submission')

    built_at       = models.DateTimeField()
    build_duration = models.TimeField()
    size           = models.IntegerField()

    # enabled and disabled use flags (should be disjoint):
    # TODO: useplus <intersection> useminus should == []
    useplus  = models.ManyToManyField(UseFlag, blank=True, related_name='installation_plus')
    useminus = models.ManyToManyField(UseFlag, blank=True, related_name='installation_minus')
    useunset = models.ManyToManyField(UseFlag, blank=True, related_name='installation_unset')

    # keyword used:
    keyword = models.ForeignKey(Keyword)

    # TODO:
    # def __unicode__(self):
    #     return "Installation: cpv '%s' installed at '%s' with '%s' use flags." % (atom, datetime, useflags)

class Selection(models.Model):
    """
    USE flags for an atom.
    """

    atom       = models.ForeignKey(Atom)
    submission = models.ForeignKey('Submission')

    useplus  = models.ManyToManyField(UseFlag, blank=True, related_name='selection_plus')
    useminus = models.ManyToManyField(UseFlag, blank=True, related_name='selection_minus')
    useunset = models.ManyToManyField(UseFlag, blank=True, related_name='selection_unset')

    def __unicode__(self):
        return "TODO"

class PackageSet(models.Model):
    name  = models.CharField(max_length=128)
    owner = models.ForeignKey('Submission')

    packages = models.ManyToManyField(Package, related_name='parentset')
    subsets  = models.ManyToManyField( 'self'
                                     , symmetrical  = False
                                     , related_name = 'parentset'
    )

    class Meta():
        unique_together = ('name', 'owner')

    # TODO:
    # def __unicode__(self):
    #     return "AtomSet '%s' with '%s' atoms owned by '%s'" % (name, atoms, owner)

class Submission(models.Model):
    host     = models.ForeignKey(Host)
    ip_addr  = models.GenericIPAddressField()
    fwd_addr = models.GenericIPAddressField(blank=True) # X-Forwarded-For
    datetime = models.DateTimeField(auto_now_add=True)
    protocol = models.IntegerField()

    # This is used for testing ATM.
    deleted  = models.BooleanField(default=False, db_index=True)

    # The email can change between submissions, so let's store it here.
    # Also, let's 'accept' invalid email addresses for the time being.
    email    = models.EmailField(blank=True, max_length=256)

    # ACCEPT_KEYWORDS (Example: "~amd64")
    arch     = models.CharField(blank=True, max_length=32)

    # arch-vendor-OS-libc (Example: "x86_64-pc-linux-gnu")
    chost    = models.CharField(blank=True, max_length=64)

    # Cross-compiling variables (build/target CHOSTs):
    cbuild   = models.CharField(blank=True, max_length=64)
    ctarget  = models.CharField(blank=True, max_length=64)

    # Platform (Example: "Linux-3.2.1-gentoo-r2-x86_64-Intel-R-_Core-TM-_i3_CPU_M_330_@_2.13GHz-with-gentoo-2.0.3")
    platform = models.CharField(blank=True, max_length=256)

    # Active Gentoo profile:
    profile  = models.CharField(blank=True, max_length=128)

    # System locale (Example: "en_US.utf8")
    lang     = models.ForeignKey(Lang, blank=True, null=True, related_name='submissions')

    # Last sync time:
    lastsync = models.DateTimeField(blank=True)

    # make.conf:
    makeconf = models.TextField(blank=True)

    # cc flags, c++ flags, ld flags, cpp flags, and fortran flags:
    cflags   = models.CharField(blank=True, max_length=128)
    cxxflags = models.CharField(blank=True, max_length=128)
    ldflags  = models.CharField(blank=True, max_length=128)
    cppflags = models.CharField(blank=True, max_length=128)
    fflags   = models.CharField(blank=True, max_length=128)

    # Portage features (enabled in make.conf):
    features = models.ManyToManyField(Feature, blank=True, null=True, related_name='submissions')

    # make.conf example: SYNC="rsync://rsync.gentoo.org/gentoo-portage"
    sync     = models.ManyToManyField(SyncServer, blank=True, null=True, related_name='submissions')

    # make.conf example: GENTOO_MIRRORS="http://gentoo.osuosl.org/"
    mirrors  = models.ManyToManyField(MirrorServer, blank=True, null=True, related_name='submissions')

    global_use      = models.ManyToManyField(UseFlag, blank=True, null=True, related_name='submissions')
    global_keywords = models.ManyToManyField(Keyword, blank=True, null=True, related_name='submissions')

    installed_packages = models.ManyToManyField(Package, blank=True, null=True, related_name='submissions_installed', through=Installation)
    selected_atoms     = models.ManyToManyField(Atom, blank=True, null=True, related_name='submissions_selected', through=Selection)

    # misc. make.conf variables:
    makeopts      = models.CharField(blank=True, max_length=128)
    emergeopts    = models.CharField(blank=True, max_length=256)
    syncopts      = models.CharField(blank=True, max_length=256)
    acceptlicense = models.CharField(blank=True, max_length=256)

    @models.permalink
    def get_absolute_url(self):
        return ('TODO', (), {'id': self.id})

    def __unicode__(self):
        return "Submission from %s made at %s" % (self.host, self.datetime)
