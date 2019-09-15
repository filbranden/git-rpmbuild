# git-rpmbuild

Build RPM packages from Development Trees.

Use RPMs to deploy and test development versions of your package, during your
development cycle. Quickly build RPM packages, using incremental builds from
your worktree. Use RPM to install the packages locally and easily rollback by
downgrading back to the distro packages.

## Using git-rpmbuild for development

In order to use git-rpmbuild, simply check out a development tree from the
upstream git repository. Create and check out your own development branches, add
your own commits and maybe even keep uncommitted changes on your worktree.

Then build RPM packages for your package using:

```
$ git rpmbuild
```

This will then detect which package you're building and download the RPM
specfile from Fedora, and use that specfile to build RPM packages using the
development sources from your worktree.

The build is incremental, so it's typically pretty quick if you're only
modifying a handful of files in the project in between each build, since only
those files and the targets that depend on them need to be rebuilt each time.

Once the RPMs are built, you can install them using:

```
$ sudo rpm -Fvh ~/rpmbuild/RPMS/*/mypackage-*.rpm
```

The RPM "Release:" part of the version is used both to prefer latest versions on
installs (making it easy to accumulate builds around) and to keep enough
information on each package to track it back to the sources.

The "Release:" field will include a full timestamp (`YYYYMMDDHHMMSS`), so that
more recent builds will be considered newer. The `rpm -F` command will prefer
those, so when you use it on an `RPMS/` directory with many builds, the latest
one will be installed by it.

Furthermore, "Release:" will include the output of `git describe`, which
typically includes the closest tag (which is typically used for the upstream
version), plus the name of the local branch checked out (so if you're using
feature branches, you can recognize which of them was used in a specific set of
packages you built.)

If you'd like to rollback an install, back to the packages shipped by your
distribution, you can then use the following command:

```
$ sudo dnf downgrade mypackage
```

The 14-digit timestamp also makes it likely that the `git rpmbuild` packages
will have a higher version than the distribution packages, so normally `dnf` or
`yum` will not replace them, even if the distribution has released newer
releases of that same package. (It is possible that the distro packages will
become newer if they release a new major version, though.)

## Advantages of git-rpmbuild over direct local install

There are many advantages of using `git rpmbuild` over installing binaries
locally using `sudo ninja install` or `sudo make install`.

Some of the advantages of this approach are:

- **Same build configuration as the distro:** Since the build is using the
  instructions from the RPM specfile, the `./configure` or `meson` invocation
  will incorporate all the options used in the build of the package for your
  distribution, such as the typical directories (prefix, bindir, libdir, etc.)
  as well as configuration options to enable/disable certain features.

- **Integrity of package and binaries on the system:** Since a package is being
  installed (instead of binaries from a local build replacing existing binaries
  owned by specific packages), the RPM database will show that everything looks
  correct. In particular, you can use the `rpm -V` command to verify that the
  files owned by your package have not been replaced or tampered with, which
  will work correctly since the RPMs installed have the correct checksums of the
  binaries built from the development tree.

- **Properly handling configuration files:** Configuration files will be handled
  in the same way as RPM upgrades from the distro, with `.rpmnew` and `.rpmsave`
  files, rather than blindingly replacing them with defaults from the
  development tree, which could easily happen if installing directly from the
  tree to the system root filesystem.

- **Easy to track currently running version:** By looking at the package name,
  you can quickly see which branch was checked out when these binaries were
  built, and using the information from `git describe` also present in the
  "Release:" field, it is possible to check out the exact commit that was used
  for this particular build.

- **Ability to rollback and to switch builds:** Rolling back is easy using a
  command such as `dnf downgrade` to go back to the packages from the distro. It
  is also possible to keep multiple development builds and switch between them,
  by simply using `rpm -U --oldpackage` to install a previous build, with no
  need to check out a different branch on the source tree and rebuild those
  binaries, or to keep multiple git worktrees around.

- **Less interference from the normal distro package upgrades**: If you're
  installing binaries over an existing package, if an upgrade for that package
  becomes available and the machine has automatic updates configured, it will
  most likely clobber the local binaries while installing that upgrade. By
  having the development binaries installed through an RPM with a version string
  that is most likely to be much larger than the one from the distro, it's
  unlikely that newer distro packages will replace the development ones, thus
  preventing them from being inadvertently replaced back with the release
  version of the package while you were meaning to test the new version.

- **Ability to install development binaries on other machines:** This is often
  useful in machines that do not have a development environment present (so
  wouldn't be able to run `make install` or `ninja install`, etc.) By building
  packages from the development sources, it's easy to ship the packages to those
  machines and simply install them using `rpm` or `dnf`, the tools that will be
  already present there.

## Advantages of git-rpmbuild over building a full RPM

There are other similar approaches that involve creating RPM packages from
development trees (such as
[`packit`](https://github.com/packit-service/packit)), but those typically
involve packing the sources into an archive, building an SRPM and rebuilding
that from scratch every time.

This can be pretty time consuming, even when using caching for the compilation
steps (`ccache`). That makes these methods great for scheduled builds (nightly,
weekly) and for background batch methods (integration testing, etc.) But they're
not great for development, when you're trying to build repeatedly and shaving
time off your commit/build/deploy/test cycle can improve your productivity
significantly.

To illustrate the difference in both methods, see the videos below. To build
systemd RPMs from the SRPM package takes over 5 minutes on a fairly capable
laptop:

[![asciicast](https://asciinema.org/a/268330.svg)](https://asciinema.org/a/268330)

Using a tool that would build a full-blown SRPM would take even longer, since
the `git archive` step must also be performed to generate an SRPM from the
worktree.

On the other hand, to build those RPMs from a local development tree using
`git rpmbuild` takes under 1 minute, since the build is incremental:

[![asciicast](https://asciinema.org/a/268520.svg)](https://asciinema.org/a/268520)

Note that it only takes 45 seconds, yet there is time to run all the tests and
save all the RPM packages on disk. Bringing 5 minutes down to 1 minute make
quite a difference when you're actively developing and need a quick turnaround!

## How does it work

It works by leveraging two arguments of `rpmbuild`:

- `--build-in-place`: Build from locally checked out sources. Sets `_builddir`
  to point to the current working directory.

- `--noprep`: Skip the `%prep` step altogether. This means not only the source
  tarball is not unpacked, but any patches from the RPM specfile will not be
  applied.

Together, these result in a local build being performed and the normal build
tools ensure an incremental build will be used, since the RPM build tree is now
the same as our development build tree.

## Installing git-rpmbuild

Pre-requisite for the code is having Python 3.7 installed and having a working
`rpmbuild` in the system, that's about it.

To work from git, simply clone the repository and make sure the `git-rpmbuild`
script is on the `$PATH`, either by adding the git worktree to `$PATH` or by
creating a symlink or copy of that script somewhere that's already in your
`$PATH` (such as `~/.local/bin`, assuming you've added it.)

I also maintain a COPR for git-rpmbuild for Fedora 30+ at:
https://copr.fedorainfracloud.org/coprs/filbranden/git-rpmbuild/

In order to use it, simply enable it with:

```
$ sudo dnf copr enable filbranden/git-rpmbuild
```

And install the package using:

```
$ sudo dnf install git-rpmbuild
```

## Limitations

There are, of course, limitations to this approach.

Only packages which perform limited actions in the `%prep` step will work with
this approach. Typically that means only unpacking the source and applying
patches for backports that are already present upstream. Since the whole `%prep`
step is skipped, the development tree must be similar enough to what the
specfile's `%build` and `%install` otherwise expect.

(Here's [an
example](https://src.fedoraproject.org/rpms/systemd/c/05bb389ca4f3e17966d240bd0ae879f3f8c443fb?branch=master)
of moving a step from `%prep` to `%install` in the specfile to solve one such
problem.)

This will also only work for packages that exist in Fedora, since that's where
the specfiles come from.

It also expects that the development worktree is close enough to what the latest
specfile is building, so that the instructions will still be applicable.
Sometimes if either development tree or specfile are having heavy changes, it's
not that easy to keep them both working in sync. Examples are files that are
shipped and not declared under `%files`, or build instructions that have changed
since the build system has been tweaked or reconfigured.

We also need the RPM build not to mess with the source tree (otherwise those
changes will mess up our development environment.) One example of problematic
package here is selinux-policy, which builds from the same tree 3 times (for
each type of policy, such as "targeted" and "strict") while replacing a handful
of files before each build. That will surely break `git-rpmbuild`.

`git-rpmbuild` also makes some assumptions about tags in the development git
repository, since it uses them to populate the "Version:" and "Release:" fields
of the built RPMs. For now, it expects tags to match a version number, possibly
including a simple "v" prefix to that number.

These packages are known to work with `git-rpmbuild`:

- `systemd`
- `numactl`
- `oomd`
- `meson`

Currently not working:

- `rpm`: Tags in the development git repository are in the format
  `rpm-${version}`, which currently wants to use `rpm` as a "Version:".
  Additionally, as of `rpm-4.15.0-alpha-69-g858d6babd`, there's a build breakage
  in `rpmmodule.c` about `variable 'moduledef' has initializer but incomplete
  type` which needs some investigation.

- `vim`: For some reason I get `error: Bad source:
  ~/.local/share/git-rpmbuild/fedora-src/vim/vim-8.1-2019.tar.bz2:
  No such file or directory`. It's expected that this file doesn't exist, but
  it's unexpected that this would break the build, since with `--noprep` no one
  should be trying to use it... I might need a version of RPM with more
  debugging available to dig into this one, but see above about that 😆.
  One more quirk of Vim is that the tags include patch number (such as
  v8.1.2026), but the Vim specfile would prefer to use simply 8.1 as the version
  and move 2026 to the "Release:" field only.

- `asciinema`: Fails with `Installed (but unpackaged) file(s) found` for a
  handful of Markdown files. Possibly easy to address in the specfile.

## Related Projects, Future Ideas, etc.

One related project is [`packit`](https://github.com/packit-service/packit), in
fact I started to look into whether I could include a feature such as this one
into `packit` itself rather than having a separate tool, but without much
success.

I would like to see a similar approach for Debian-based systems, since often I
would like to test my systems on Ubuntu or Debian and being able to use a
similar approach would be very nice. (See above for advantages.)

Obviously, having more packages working on `git-rpmbuild` is a big priority, so
feel free to report success/failure if you use it in any of your packages. PRs
addressing issues that fix build of packages you care about are also very
welcome!

I would like to use epochs to make versions of `git-rpmbuild` RPMs even newer
than distro packages, but there are some tricky cases when specfiles build
multiple packages and the packages depend on each other and they specify the
dependency with an exact version match that doesn't include any epoch...
(Parsing and generating specfiles is pretty hacky!)

More flexibility in handling the "Release:" tag would be nice.

Per-package overrides, perhaps with a dotfile at the top of the git tree, or
perhaps a local ConfigParser file somewhere in the user's home directory, would
be good if packages have special requirements that need to be configured for
those packages only.

Right now there are no command-line arguments, but it would be nice to add
options to enable or disable certain features. Examples are generation of
debuginfo and debugsource packages (currently always disabled), or whether to
run the package tests during the RPM build step (currently always enabled.)
Project name detection currently depends on the directory name, having a
command-line argument/flag or per-project config file in the git tree to
override would also be a good idea.

While the primary purpose of this package is to build RPMs in place from a
development worktree, being able to generate a SRPM as well would be nice, as
that could be then used to feed a COPR repository and to automate nightly and
weekly builds for projects.

