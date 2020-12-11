
# Build-tools overview

  The build-tools are a set of packages that are usually required to build new
  software modules. These are used for the setup of infrastructure toolboxes
  such as the
  [EBRAINS-Tools](https://wiki.ebrains.eu/bin/view/Collabs/ebrains-tools/), but
  are also available to developers do build their own toolboxes.

> The build-tools are a collection of exclusively build-time requirements.

  During the installation or deployment of software usually a set of
  dependencies needs to be available. These can be divided into build-time
  dependencies and run-time dependencies. The former are required only for the
  installation (e.g.  compilers), while the latter are required during the
  run-time of the program (e.g. dynamic libraries). For some packages this may
  not be obvious at first, as for example the GCC is usually thought of as
  compiler package, but it also brings a suite of standard libraries.


# Used concepts

## Packages

  When building tools, the "atoms" are the different tools and libraries
  (packages) in their different versions. In this scheme, the package needs to
  have an identifiable version number in order to result in a reproducible
  setup. Development versions may be considered packages, but using e.g. a git
  branch ToolA.git/master should be well considered, since it must be
  considered unstable and likely leads to an unreproducible software stack.

  ![Packages.png]()

  The point is the *permanent tag for the state of the software* that is used,
  and there is no specific requirement on the versioning scheme per se (may be
  [versioned](https://en.wikipedia.org/wiki/Software_versioning) releases,
  Software-DOIs (e.g. by [zenodo.org](https://zenodo.org)), etc).


## Builds

  Each tool or library usually requires a set of dependencies to be available
  and may additionally have different options that influence the tree of
  dependencies. A *build* is in this context considered to be a specific
  package/version that is built with a particular choice of dependencies.
  Meaning that builds of the same package/version with different dependencies
  or options are considered different builds.

  ![Build.png]()

  Roughly speaking, a build sets up the required build environment and then
  builds the tool. The environment is the joint set of available software
  during the build time. These are the system provided tools and any optionally
  loaded modules.

  ```bash
  module load LibraryD/2020.1
  module load LibraryE/4.2\_rc1
  module load ToolA/1.2

  build ToolB/0.3 {{/code}}
  ```

  Separating the actual build step from the loading of the requirements,
  distinguishes this workflow from conventional packaging systems (like apt,
  conda, pip, etc.), because the build does not pull in the dependencies
  automatically.

> The dependencies are selected by the *build*, not by the *package*.

  This gives direct control over the dependencies and helps to identify
  dependency conflicts as early as possible, on the level of the build process,
  instead of the usually later problems in the deployment step.  Preparing
  Builds can be done in testing areas by the tool development teams, which have
  knowledge about the nature of the dependencies and the options in the build
  process.

  The separate build step also leaves all control to the developer teams
  regarding the updates of tools and dependencies. Dependencies may be provided

  * by the **base system**,
  * build "**locally**" in a testing area, as well as
  * selected from an available (and ideally agreed upon) **central toolbox**.

  Build definitions that work in a testing area can easily be transferred into
  common toolboxes to be used by more developers.


## Deployments

  Given numerous packages in different versions and with various dependencies
  the number of possible Builds is driven by the development teams. Selecting
  sets of Builds for one or more toolboxes is then a comparatively easy task in
  the deployment stage.

> A *Deployment* is a collection of *Builds*.

  The deployment process needs to run the builds ordered by their dependencies.
  In contrast to conventional systems, deployments however do not need to do
  *dependency resolution*, since the dependencies are fixed by the build. The
  most important effect of this is, that **no dependencies are automatically
  pulled in**. This allows a Build to depend on system provided packages as
  well as explicitly built packages in the deployment.

  ![Deployment.png]()

  Prime example would be the choice of MPI implementation. On HPC sites usually
  a specialized implementation of MPI is available that is tailored to the
  particular hardware installed. On a laptop or few-machine cluster you may
  however want to choose different standard implementations and compare
  resulting performance. In standard package managers a dependency on
  proprietary implementations is difficult to realize.

  Defining different site.config files for both setups allows the user to keep
  system level differences at the software installation stage, instead of
  requiring this at each run-time. Consider following example:

  * **HPC site**

    site.config
    ```yaml
    nest-simulator:
    - parastationMPI           # system provided
    - gcc-9.6-x86\_64\_special # system provided
    ```

    usage:
    ```bash
    $ module load nest-simulator
    $ python
    >>> import nest
    ```

  * **Laptop/local cluster**

    site.config
    ```yaml
    openmpi:
    - gcc/10.2.0 \# system provided

    nest-simulator:
    - openmpi \# built in this deployment
    - gcc/10.2.0 \# system provided
    ```

    usage:
    ```bash
    $ module load nest-simulator
    $ python
    >>> import nest
    ```

  In this example the HPC site deployment would only build the application
  depending on system provided modules. On the users laptop or local cluster
  one may want to explicitly install a standard MPI variant and build the MPI
  package in addition to the application (of course this is equally possible on
  HPC, but less recommended).

  When it comes to the usage of the application the user profits from a high
  degree of symmetry. Even though different backing libraries are used the user
  can run the same commands, as the application modulefiles pull in
  requirements specific for the site automatically. This frees the user from
  the requirement to know which specific compiler to use and which
  implementation of library to choose.

> The usage of the application can be made consistent on all sites.


# Conclusion

  The Package/Build/Deployment system behaves very different from usual package
  managers. It specifically targets developers admins and users, by separating
  the large set of decisions on the way from code to user into smaller
  dedicated sets right for each target group. Any problems during the process
  should always come up at the group with the highest expertise.

  * The developers provide packages and can easily test the build process by
    creating custom Builds. They are able to fix the problems in their
    software.
  * The admins can use Builds that have been proven against packages in the
    standard set. They know what goes where.
  * The user can choose from packages provided centrally and from specially
    built toolboxes when directly in contact with developers. The workflows can
    be easily expressed with the minimum required information.

  The overall system requires more than "click-the-button" expertise, but it
  shifts this requirement towards the group that can most easily solve it,
  having the choice of options on the same level as the expertise. The
  de-central nature of the Builds and central nature of the "official"
  toolboxes allows for diverse development processes combined with the
  stabilizing effect of editorial control over the most commonly used tools.
