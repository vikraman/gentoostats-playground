from django.db import IntegrityError, models
from django.core.validators import RegexValidator, URLValidator, validate_email
from django.core.exceptions import ValidationError

from portage.dep import Atom as PortageAtom
from portage.exception import InvalidAtom
from portage._sets import SETPREFIX

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
                           , max_length  = 31
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
                           , max_length  = 63
                           , validators  = [package_name_validator]
    )

    def __unicode__(self):
        return self.name

class Repository(models.Model):
    name = models.CharField(max_length=63, db_index=True)
    url  = models.CharField(max_length=255, db_index=True, blank=True)

    # method   = models.CharField(max_length=31)  # e.g. "git"
    # priority = models.IntegerField()            # e.g. 50
    # quality  = models.CharField(max_length=31)  # e.g. "experimental"
    # status   = models.CharField(max_length=31)  # e.g. "official"

    # description
    # owner
    # feed

    class Meta:
        unique_together = ('name', 'url')

    def get_absolute_url(self):
        return "TODO"

    def __unicode__(self):
        return self.name

version_validator = RegexValidator('^\S+$')
slot_validator    = RegexValidator('^\S+$')

def atom_validator(atom):
    try:
        PortageAtom(atom)
    except InvalidAtom:
        raise ValidationError('%s is not a valid atom' % (atom))
    except:
        raise ValidationError('Something went wrong when validating %s.' % (atom))

class AtomABC(models.Model):
    """
    Abstract base class for atoms.

    Consists of:
      operator                         (optional)  (not defined here)
      category                         (mandatory)
      package name                     (mandatory)
      version (plus optional revision) (optional)  (not defined here)
      slot                             (optional)
      repository                       (optional)
      use flag choices                 (optional)  (not defined here)

    For more Slotting info, please see
    http://devmanual.gentoo.org/general-concepts/slotting/index.html

    Consult ebuild(5) if in doubt.
    """

    category = models.ForeignKey( Category
                                , related_name = '+'
    )

    package_name = models.ForeignKey( PackageName
                                    , related_name = '+'
    )

    slot = models.CharField( max_length = 31
                           , blank      = True
                           , null       = True
                           , validators = [slot_validator]
    )

    repository = models.ForeignKey( Repository
                                  , blank        = True
                                  , null         = True
                                  , related_name = '+'
    )

    class Meta:
        abstract = True

# TODO: remove the blank=True things when the client is patched.
class Package(AtomABC):
    """
    Like AtomABC, but with a mandatory version.

    Note that you can't override parent fields in Django.
    """

    # version also holds the revision specified (if there's any)
    version = models.CharField(max_length=31, validators=[version_validator])

    class Meta:
        unique_together = ( 'category'
                          , 'package_name'
                          , 'version'
                          , 'slot'
                          , 'repository'
        )

    @models.permalink
    def get_absolute_url(self):
        # TODO
        return ('package_details_url', (), {'id': self.id})

    def __unicode__(self):
        slot       = ":%s"  % (self.slot)       if self.slot                            else ''
        repository = "::%s" % (self.repository) if self.repository != DEFAULT_REPO_NAME else ''

        return "=%s/%s-%s%s%s" % ( self.category
                                 , self.package_name
                                 , self.version
                                 , slot
                                 , repository
        )

class Atom(AtomABC):
    """
    Like AtomABC, but optionally: without a version, with an operator, and with
    use flag specifications.
    """

    # TODO: handle blockers ('!!', '!').
    # TODO: handle use flag specifications ('vim[X]').

    # '', '~', '=', '>', '<', '=*', '>=', or '<='. Consult ebuild(5).
    ATOM_OPERATORS = (
        ('',   'None'),               #
        ('~',  'Any revision'),       # prefix
        ('=',  'Equals'),             # prefix
        ('>',  'Greater than'),       # prefix
        ('<',  'Less than'),          # prefix
        ('>=', 'GE'),                 # prefix
        ('<=', 'LE'),                 # prefix
        ('=*', 'Version glob match'), # '=' prefix + '*' postfix
    )

    full_atom = models.CharField( primary_key = True
                                , max_length  = 63
                                , validators  = [atom_validator]
    )

    operator = models.CharField( max_length = 2
                               , blank = True
                               , choices = ATOM_OPERATORS
                               , default=''
    )

    version = models.CharField( max_length = 31
                              , blank      = True
                              , validators = [version_validator]
    )

    class Meta:
        unique_together = ( 'category'
                          , 'package_name'
                          , 'version'
                          , 'slot'
                          , 'repository'
                          , 'full_atom'
                          , 'operator'
        )

    @models.permalink
    def get_absolute_url(self):
        # TODO
        return ('atom_details_url', (), {'id': self.id})

    def __unicode__(self):
        return self.full_atom

use_flag_validator = RegexValidator('^\S+$')
class UseFlag(models.Model):
    """
    A USE flag.
    """

    name = models.CharField( primary_key = True
                           , max_length  = 63
                           , validators  = [use_flag_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

lang_validator = RegexValidator('^\S+$') # TODO
class Lang(models.Model):
    """
    System $LANG.
    """

    name = models.CharField( primary_key = True
                           , max_length  = 31
                           , validators  = [lang_validator]
    )

    def __unicode__(self):
        return self.name

# UUID format: 8-4-4-4-12 groups of hex.
uuid_validator = RegexValidator(
    '^[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}$'
)
class Host(models.Model):
    """
    A computer, identified by 32 hexadecimal digits (with hyphens, case
    insensitive).

    UUID Info: http://tools.ietf.org/html/rfc4122
               http://en.wikipedia.org/wiki/Universally_unique_identifier
    """

    id = models.CharField( primary_key = True
                         , max_length  = 36
                         , validators  = [uuid_validator]
    )

    # TODO: prevent accidental overwritting of self.uuid
    # @property
    # def uuid(self):
    #     return self.id

    # This is the 'password' required to upload stats for this host.
    upload_key = models.CharField("upload key (needed to upload stats)", max_length=63)
    # TODO: What if the user wants to change his upload_key?
    # Should we support this at all?

    # A small optimisation:
    # latest_submission = models.ForeignKey( 'Submission'
    #                                      , related_name = '+'
    #                                      , null         = True
    #                                      , default      = None
    # )

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

    # TODO: make this case insensitive?

    name = models.CharField( primary_key = True
                           , max_length  = 63
                           , validators  = [feature_validator]
    )
    added_on = models.DateTimeField(auto_now_add=True)

    @models.permalink
    def get_absolute_url(self):
        # TODO
        return ('feature_details_url', (), {'feature': self.name})

    def __unicode__(self):
        return self.name

class MirrorServer(models.Model):
    # url = models.URLField(primary_key=True, max_length=255)
    url = models.CharField(primary_key=True, max_length=255)

    def __unicode__(self):
        return self.url

# sync_server_validator = TODO
class SyncServer(models.Model):
    # By default URLField does not like urls starting with 'rsync://'.
    url = models.CharField(primary_key=True, max_length=255)

    def __unicode__(self):
        return self.url

# TODO: add validator
class Keyword(models.Model):
    name     = models.CharField(primary_key=True, max_length=127)
    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class Installation(models.Model):
    """
    Package installations on hosts.
    """

    package    = models.ForeignKey(Package)
    submission = models.ForeignKey('Submission')

    # yes, blank must be True
    built_at       = models.DateTimeField(blank=True, null=True)
    build_duration = models.IntegerField(blank=True, null=True)
    size           = models.IntegerField(blank=True, null=True)

    # TODO: better documentation and verification
    use_iuse   = models.ManyToManyField(UseFlag, blank=True, related_name='installation_iuse')
    use_pkguse = models.ManyToManyField(UseFlag, blank=True, related_name='installation_pkguse')
    use_final  = models.ManyToManyField(UseFlag, blank=True, related_name='installation_final')

    # keyword used:
    keyword = models.ForeignKey(Keyword)

    # TODO:
    def __unicode__(self):
        return "'%s' installed at '%s'" % (self.package, self.built_at)

class AtomSet(models.Model):
    name  = models.CharField(max_length=127)
    owner = models.ForeignKey('Submission')

    atoms   = models.ManyToManyField(Atom, related_name='parent_set')
    subsets = models.ManyToManyField( 'self'
                                    , symmetrical  = False
                                    , blank        = True
                                    , related_name = 'parent_set'
    )

    class Meta():
        unique_together = ('name', 'owner')

    # def __unicode__(self):
    #     return "'%s' (has '%d' atoms and '%d' subsets, owned by '%s')" % \
    #         (self.name, self.atoms.count(), self.subsets.count(), self.owner)

    def __unicode__(self):
        return "%s%s" % (SETPREFIX, self.name)

class Submission(models.Model):
    raw_request_filename = models.CharField(max_length=127, unique=True)

    host     = models.ForeignKey(Host, related_name='submissions')
    ip_addr  = models.GenericIPAddressField()
    fwd_addr = models.GenericIPAddressField(blank=True, null=True) # X-Forwarded-For
    datetime = models.DateTimeField(auto_now_add=True)
    protocol = models.IntegerField()

    # This is used for testing ATM.
    deleted  = models.BooleanField(default=False, db_index=True)

    # The email can change between submissions, so let's store it here.
    # Also, let's 'accept' invalid email addresses for the time being.
    email    = models.EmailField(blank=True, null=True, max_length=255)

    # ACCEPT_KEYWORDS (Example: "~amd64")
    arch     = models.CharField(blank=True, null=True, max_length=31)

    # arch-vendor-OS-libc (Example: "x86_64-pc-linux-gnu")
    chost    = models.CharField(blank=True, null=True, max_length=63)

    # Cross-compiling variables (build/target CHOSTs):
    cbuild   = models.CharField(blank=True, null=True, max_length=63)
    ctarget  = models.CharField(blank=True, null=True, max_length=63)

    # Platform (Example: "Linux-3.2.1-gentoo-r2-x86_64-Intel-R-_Core-TM-_i3_CPU_M_330_@_2.13GHz-with-gentoo-2.0.3")
    platform = models.CharField(blank=True, null=True, max_length=255)

    # Active Gentoo profile:
    profile  = models.CharField(blank=True, null=True, max_length=127)

    # System locale (Example: "en_US.utf8")
    lang     = models.ForeignKey(Lang, blank=True, null=True, related_name='submissions')

    # Last sync time:
    lastsync = models.DateTimeField(blank=True, null=True)

    # make.conf:
    makeconf = models.TextField(blank=True, null=True)

    # cc flags, c++ flags, ld flags, cpp flags, and fortran flags:
    cflags   = models.CharField(blank=True, null=True, max_length=127)
    cxxflags = models.CharField(blank=True, null=True, max_length=127)
    ldflags  = models.CharField(blank=True, null=True, max_length=127)
    cppflags = models.CharField(blank=True, null=True, max_length=127)
    fflags   = models.CharField(blank=True, null=True, max_length=127)

    # Portage features (enabled in make.conf):
    features = models.ManyToManyField(Feature, blank=True, related_name='submissions')

    # make.conf example: SYNC="rsync://rsync.gentoo.org/gentoo-portage"
    sync     = models.ForeignKey(SyncServer, blank=True, null=True, related_name='+')

    # make.conf example: GENTOO_MIRRORS="http://gentoo.osuosl.org/"
    mirrors  = models.ManyToManyField(MirrorServer, blank=True, related_name='submissions')

    global_use      = models.ManyToManyField(UseFlag, blank=True, related_name='submissions')
    global_keywords = models.ManyToManyField(Keyword, blank=True, related_name='submissions')

    installed_packages = models.ManyToManyField(Package, blank=True, related_name='submissions', through=Installation)
    selected_sets      = models.ManyToManyField(AtomSet, blank=True, related_name='submissions')

    # misc. make.conf variables:
    makeopts      = models.CharField(blank=True, null=True, max_length=127) # MAKEOPTS
    emergeopts    = models.CharField(blank=True, null=True, max_length=255) # EMERGE_DEFAULT_OPTS
    syncopts      = models.CharField(blank=True, null=True, max_length=255) # PORTAGE_RSYNC_EXTRA_OPTS
    acceptlicense = models.CharField(blank=True, null=True, max_length=255) # ACCEPT_LICENSE

    @models.permalink
    def get_absolute_url(self):
        return ('TODO', (), {'id': self.id})

    def __unicode__(self):
        return "Submission from %s made at %s" % (self.host, self.datetime)
