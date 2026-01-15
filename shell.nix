# https://nix.dev/tutorials/declarative-and-reproducible-developer-environments
with import <nixpkgs> { };

mkShell {

  # Package names can be found via https://search.nixos.org/packages
  nativeBuildInputs = [
    direnv
		glibc
		# qt5.qtwayland

		python313
		python313Packages.pip
		python313Packages.virtualenv

		python313Packages.yt-dlp
		python313Packages.requests
		python313Packages.beautifulsoup4
		python313Packages.aiosqlite
		python313Packages.eyed3
		python313Packages.ytmusicapi
		python313Packages.pyqt6
		python313Packages.pytaglib
  ];

  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  NIX_ENFORCE_PURITY = true;
}
