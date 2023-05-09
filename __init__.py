# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GenerateSwmmInp
                                 A QGIS plugin
 This plugin generates SWMM Input files
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        copyright            : (C) 2023 by Jannik Schilling
        email                : jannik.schilling@posteo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
__author__ = 'Jannik Schilling'
__date__ = '2023-05-09'
__copyright__ = '(C) 2023 by Jannik Schilling'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GenerateSwmmInp class from file SwmmGenerator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .generate_swmm_inp_plugin import GenerateSwmmInp
    return GenerateSwmmInp()
