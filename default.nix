##
## This file is part of the deploy-wrt project.
##
## Copyright (C) 2024 Joel Holdsworth <joel@airwebreathe.org.uk>
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

{ python3
}: python3.pkgs.buildPythonApplication {
  pname = "deploy-wrt";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python3.pkgs; [ setuptools ];

  doInstallCheck = true;
}