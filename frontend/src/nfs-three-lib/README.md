# nfs-three-lib

three.js code shared by TailsLab's GUI and the nfs-web game. TailsLab's `frontend/src/nfs-three-lib/` is the source:
it is copied into nfs-web's `src/common/nfs-three-lib/` as it is. Change it in TailsLab, then copy it over.

- Files here import only each other (relative paths) and the packages `three`, `@gg-web-engine/core` and `rxjs`:
  nothing from the rest of TailsLab or of nfs-web, no Angular, no path aliases. A part they need from outside is
  brought here.
- No specs here (nfs-web runs none): TailsLab tests these files next to the GUI components that use them.
