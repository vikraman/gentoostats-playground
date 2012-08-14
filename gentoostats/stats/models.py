from portage.dep import Atom as PortageAtom
from portage.exception import InvalidAtom
from portage._sets import SETPREFIX as SET_PREFIX

from django.db import models
from django.db.models import Max, Count
from django.core.validators import RegexValidator, URLValidator, validate_email
from django.core.exceptions import ValidationError

# I have tried being consistent with the names defined here:
# http://devmanual.gentoo.org/ebuild-writing/variables/index.html
#
# Atom syntax: operator cat / package_name - version - revision star_operator : slot :: repo [use_flags]
# Examples:    =sys-devel/gcc-4.6.1-r1:4.6::toolchain[cxx(-)]
#              =www-client/google-chrome-18*

DEFAULT_REPO_NAME = 'gentoo'

# 'virtual' match idea taken from euscan. Thanks, fox!
category_validator = RegexValidator(r'^(?:\w+-\w+)|virtual$')
class Category(models.Model):
    name = models.CharField( primary_key = True
                           , max_length  = 31
                           , validators  = [category_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stats:category_details_url', (), {'category': self.name})

package_name_validator = RegexValidator(r'^\S+$')
class PackageName(models.Model):
    name = models.CharField( primary_key = True
                           , max_length  = 63
                           , validators  = [package_name_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class Repository(models.Model):
    name = models.CharField(max_length=63, db_index=True)
    url  = models.CharField(max_length=255, db_index=True, blank=True, null=True)

    added_on = models.DateTimeField(auto_now_add=True)

    # method   = models.CharField(max_length=31)  # e.g. "git"
    # priority = models.IntegerField()            # e.g. 50
    # quality  = models.CharField(max_length=31)  # e.g. "experimental"
    # status   = models.CharField(max_length=31)  # e.g. "official"

    # description
    # owner
    # feed

    class Meta:
        unique_together = ('name', 'url')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stats:repository_details_url', (), {'url': self.url})

version_validator = RegexValidator(r'^\S+$')
slot_validator    = RegexValidator(r'^\S+$')

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

    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Package(AtomABC):
    """
    Like AtomABC, but with a mandatory version.

    Note that you can't override parent fields in Django.
    """

    # version also holds the revision specified (if there's any)
    version = models.CharField(max_length=31, validators=[version_validator])

    # category + package_name, denormalised and indexed for performance:
    cp = models.CharField(max_length=95, unique=True, db_index=True)

    class Meta:
        unique_together = ( 'category'
                          , 'package_name'
                          , 'version'
                          , 'slot'
                          , 'repository'
        )

        ordering = ['category', 'package_name', 'version', 'slot']

    def __unicode__(self):
        slot       = ":%s"  % (self.slot)       if self.slot                            else ''
        repository = "::%s" % (self.repository) if self.repository != DEFAULT_REPO_NAME else ''

        return "=%s/%s-%s%s%s" % ( self.category
                                 , self.package_name
                                 , self.version
                                 , slot
                                 , repository
        )

    def save(self, *args, **kwargs):
        self.cp = self.category.name + '/' + self.package_name.name
        super(Package, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        # TODO:
        return ('stats:package_details_url', (), {
            'category': self.category,
            'package_name': self.package_name,
            'version': self.version,
            'slot': self.slot,
            'repository': self.repository,
        })

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

        ordering = ['category', 'package_name', 'version', 'slot']

    def __unicode__(self):
        return self.full_atom

    @models.permalink
    def get_absolute_url(self):
        # TODO
        return ('stats:atom_details_url', (), {'id': self.id})

use_flag_validator = RegexValidator(r'^[+\-]?\w[\w@\-+]*$')
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

    @models.permalink
    def get_absolute_url(self):
        return ('stats:useflag_details_url', (), {'useflag': self.name})

    @property
    def num_submissions(self):
        return Submission.objects.filter(global_use__name=self.name).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(global_use__name=self.name).order_by()\
                .aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(global_use__name=self.name).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

lang_validator = RegexValidator(r'^\S+$') # TODO
class Lang(models.Model):
    """
    System $LANG.
    """

    name = models.CharField( primary_key = True
                           , max_length  = 31
                           , validators  = [lang_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @property
    def num_submissions(self):
        return Submission.objects.filter(lang__name=self.name).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(lang__name=self.name).order_by()\
                .aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(lang__name=self.name).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

# UUID format: 8-4-4-4-12 groups of hex.
uuid_validator = RegexValidator(
    r'^(i?)[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$'
)
class Host(models.Model):
    """
    A computer, identified by 32 hexadecimal digits (with hyphens, case-
    sensitive). Make sure to store the UUID in lowercase to make this
    case-insensitive.

    UUID Info: http://tools.ietf.org/html/rfc4122
               http://en.wikipedia.org/wiki/Universally_unique_identifier
    """

    id = models.CharField( primary_key = True
                         , max_length  = 36
                         , validators  = [uuid_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

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

    def __unicode__(self):
        return self.id

    @models.permalink
    def get_absolute_url(self):
        return ('stats:host_details_url', (), {'host_id': self.id})

    @property
    def latest_submission(self):
        # TODO: Determine whether all hosts should have at least one submission.

        try:
            return self.submissions.latest('datetime')
        except Exception as e:
            return None

    @property
    def submission_history(self):
        return self.submissions.order_by('datetime')\
                .values_list('id', 'datetime', 'protocol')

feature_validator = RegexValidator(r'^\S+$')
class Feature(models.Model):
    """
    A Portage FEATURE.
    """

    # TODO: make this case insensitive (like Host.id)?

    name = models.CharField( primary_key = True
                           , max_length  = 63
                           , validators  = [feature_validator]
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stats:feature_details_url', (), {'feature': self.name})

    @property
    def num_submissions(self):
        return Submission.objects.filter(features__name=self.name).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(features__name=self.name).order_by()\
                .aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(features__name=self.name).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

class MirrorServer(models.Model):
    # url = models.URLField(unique=True, max_length=255)
    url = models.CharField(unique=True, max_length=255)

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.url

    @models.permalink
    def get_absolute_url(self):
        return ('stats:mirror_details_url', (), {'mirror': self.url})

    @property
    def num_submissions(self):
        return Submission.objects.filter(mirrors__url=self.url).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(mirrors__url=self.url).order_by()\
                .aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(mirrors__url=self.url).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

# sync_server_validator = TODO
class SyncServer(models.Model):
    # By default URLField does not like urls starting with 'rsync://'.
    url = models.CharField(unique=True, max_length=255)

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.url

    @models.permalink
    def get_absolute_url(self):
        return ('stats:sync_details_url', (), {'sync': self.url})

    @property
    def num_submissions(self):
        return Submission.objects.filter(sync__url=self.url).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(sync__url=self.url).order_by()\
                .aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(sync__url=self.url).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

# TODO: add validator
class Keyword(models.Model):
    name     = models.CharField(primary_key=True, max_length=127)

    added_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stats:keyword_details_url', (), {'keyword': self.name})

    @property
    def num_submissions(self):
        return Submission.objects.filter(global_keywords__name=self.name).count()

    @property
    def num_all_hosts(self):
        return Submission.objects.filter(global_keywords__name=self.name)\
                .order_by().aggregate(Count('host', distinct=True)).values()[0]

    @property
    def num_hosts(self):
        return Submission.objects.latest_submissions\
                .filter(global_keywords__name=self.name).count()

    @property
    def num_previous_hosts(self):
        return self.num_all_hosts - self.num_hosts

class Installation(models.Model):
    """
    Package installations on hosts.

    It is expected that each installation is unique to each host, but that may
    not always hold true.
    """

    package = models.ForeignKey(Package, related_name='installations')

    # keyword used:
    keyword = models.ForeignKey(Keyword)

    built_at       = models.DateTimeField(blank=True, null=True)
    build_duration = models.IntegerField(blank=True, null=True)
    size           = models.BigIntegerField(blank=True, null=True)

    # TODO: better documentation and verification
    iuse   = models.ManyToManyField(UseFlag, blank=True, related_name='installations_iuse')
    pkguse = models.ManyToManyField(UseFlag, blank=True, related_name='installations_pkguse')
    use    = models.ManyToManyField(UseFlag, blank=True, related_name='installations_use')

    class Meta():
        ordering = ['package', 'built_at']

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
        return "%s%s" % (SET_PREFIX, self.name)

class SubmissionManager(models.Manager):
    use_for_related_fields = True

    @property
    def latest_submission_ids(self):
        """
        Return the latest submission IDs of each host (ordered by PK).
        """

        # The following will result in the following query:
        #     SELECT MAX("stats_submission"."id") AS "latest_submission_id" FROM
        #     "stats_submission" GROUP BY "stats_submission"."host_id"
        return Submission.objects.order_by().values('host')\
                .annotate(latest_submission_id=Max('id'))\
                .values_list('latest_submission_id', flat=True)

    @property
    def latest_submissions(self):
        """
        Return the latest submissions of each host (ordered by PK).
        """

        return Submission.objects.filter(pk__in=self.latest_submission_ids)

class Submission(models.Model):
    raw_request_filename = models.CharField(max_length=127, unique=True)

    host     = models.ForeignKey(Host, related_name='submissions')
    country  = models.CharField(max_length=127, blank=True, null=True)
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

    # cc flags, c++ flags, ld flags, and fortran flags:
    cflags   = models.CharField(blank=True, null=True, max_length=127)
    cxxflags = models.CharField(blank=True, null=True, max_length=127)
    ldflags  = models.CharField(blank=True, null=True, max_length=127)
    fflags   = models.CharField(blank=True, null=True, max_length=127)

    # Portage features (enabled in make.conf):
    features = models.ManyToManyField(Feature, blank=True, related_name='submissions')

    # make.conf example: SYNC="rsync://rsync.gentoo.org/gentoo-portage"
    sync = models.ForeignKey(SyncServer, blank=True, null=True, related_name='+')

    # make.conf example: GENTOO_MIRRORS="http://gentoo.osuosl.org/"
    mirrors = models.ManyToManyField(MirrorServer, blank=True, related_name='submissions')

    global_use      = models.ManyToManyField(UseFlag, blank=True, related_name='submissions')
    global_keywords = models.ManyToManyField(Keyword, blank=True, related_name='submissions')

    installations = models.ManyToManyField(
        Installation,
        blank=True,
        related_name='submissions',
    )

    reported_sets = models.ManyToManyField(
        AtomSet,
        blank=True,
        related_name='submissions',
    )

    # MAKEOPTS:
    makeopts = models.CharField(blank=True, null=True, max_length=127)

    # EMERGE_DEFAULT_OPTS:
    emergeopts = models.CharField(blank=True, null=True, max_length=255)

    # PORTAGE_RSYNC_EXTRA_OPTS:
    syncopts = models.CharField(blank=True, null=True, max_length=255)

    # ACCEPT_LICENSE:
    acceptlicense = models.CharField(blank=True, null=True, max_length=255)

    objects = SubmissionManager()

    def __unicode__(self):
        return "Submission from %s made at %s" % (self.host, self.datetime)

    @models.permalink
    def get_absolute_url(self):
        return ('stats:submission_details_url', (), {'id': self.id})

    @property
    def tree_age(self):
        """
        Returns self.datetime - self.lastsync in seconds, or None if something
        goes wrong.
        """

        if self.lastsync:
            try:
                age = int((self.datetime - self.lastsync).total_seconds())
                assert age >= 0
                return age
            except Exception as e:
                # TODO: log this
                pass

        return None
