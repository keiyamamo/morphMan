#!/usr/bin/env python

import vtk
import sys
import math
from common import *
from vmtk import vtkvmtk
from os import path


def MaskVoronoiDiagram(voronoi, centerlines):
    numberOfCenterlinesPatches = centerlines.GetNumberOfCells()
    numberOfVoronoiPoints = voronoi.GetNumberOfPoints()

    maskArray = vtk.vtkIntArray()
    maskArray.SetNumberOfComponents(1)
    maskArray.SetNumberOfTuples(numberOfVoronoiPoints)
    maskArray.FillComponent(0, 0)

    for i in range(numberOfCenterlinesPatches):
        tangent, center, centerMISR = ComputePatchEndPointParameters(i, centerlines)
        MaskWithPatch(i, tangent, center, centerMISR, maskArray, centerlines, voronoi)

    return maskArray


def ComputePatchEndPointParameters(id, centerlines):
    point0 = [0.0, 0.0, 0.0]
    point1 = [0.0, 0.0, 0.0]
    tan = [0.0, 0.0, 0.0]
    radius0 = -1

    cell = vtk.vtkGenericCell()
    centerlines.GetCell(id, cell)

    if (id == 0):
        point0 = cell.GetPoints().GetPoint(cell.GetNumberOfPoints() - 1)
        point1 = cell.GetPoints().GetPoint(cell.GetNumberOfPoints() - 2)
        radius0 = centerlines.GetPointData().GetArray(radiusArrayName).GetTuple1(cell.GetPointId(cell.GetNumberOfPoints() - 1))

    else:
        point0 = cell.GetPoints().GetPoint(0)
        point1 = cell.GetPoints().GetPoint(1)
        radius0 = centerlines.GetPointData().GetArray(radiusArrayName).GetTuple1(cell.GetPointId(0))

    tan[0] = point1[0] - point0[0]
    tan[1] = point1[1] - point0[1]
    tan[2] = point1[2] - point0[2]
    vtk.vtkMath.Normalize(tan)

    return tan, point0, radius0


def MaskWithPatch(id, t, c, r, maskArray, centerlines, voronoi):
    patch = extract_single_line(centerlines, id)

    tubeFunction = vtkvmtk.vtkvmtkPolyBallLine()
    tubeFunction.SetInput(patch)
    tubeFunction.SetPolyBallRadiusArrayName(radiusArrayName)

    lastSphere = vtk.vtkSphere()
    lastSphere.SetRadius(r * 1.5)
    lastSphere.SetCenter(c)

    for i in range(voronoi.GetNumberOfPoints()):
        point = [0.0, 0.0, 0.0]
        voronoiVector = [0.0, 0.0, 0.0]

        voronoi.GetPoint(i, point)
        voronoiVector = [point[j] - c[j] for j in range(3)]
        voronoiVectorDot = vtk.vtkMath.Dot(voronoiVector, t)

        tubevalue = tubeFunction.EvaluateFunction(point)
        spherevalue = lastSphere.EvaluateFunction(point)

        if (spherevalue < 0.0) & (voronoiVectorDot < 0.0): continue
        elif (tubevalue <= 0.0):
            maskArray.SetTuple1(i, 1)


def ComputeNumberOfMaskedPoints(dataArray):
    numberOfPoints = 0
    for i  in range(dataArray.GetNumberOfTuples()):
        value = dataArray.GetTuple1(i)
        if (value == 1): numberOfPoints += 1
    return numberOfPoints


def ExtractMaskedVoronoiPoints(voronoi,maskArray):
    numberOfPoints = ComputeNumberOfMaskedPoints(maskArray)

    maskedVoronoi = vtk.vtkPolyData()
    maskedPoints = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    radiusArray = get_vtk_array(radiusArrayName, 1, numberOfPoints)

    count = 0
    for i in range(voronoi.GetNumberOfPoints()):
        point = [0.0, 0.0, 0.0]
        voronoi.GetPoint(i, point)
        pointRadius = voronoi.GetPointData().GetArray(radiusArrayName).GetTuple1(i)
        value = maskArray.GetTuple1(i)
        if (value == 1):
            maskedPoints.InsertNextPoint(point)
            radiusArray.SetTuple1(count, pointRadius)
            cellArray.InsertNextCell(1)
            cellArray.InsertCellPoint(count)
            count += 1

    maskedVoronoi.SetPoints(maskedPoints)
    maskedVoronoi.SetVerts(cellArray)
    maskedVoronoi.GetPointData().AddArray(radiusArray)

    return maskedVoronoi
