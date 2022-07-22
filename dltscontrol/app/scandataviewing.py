""" 
Extenison which provides panel interfaces and implementations to show and depicture scan data. 

Interfaces
----------
Panels: `ImageViewerPanel`, `ScanImageViewerPanel` and `ScanImageInfoPanel`. 

Implementations
---------------
Panels: `StandardImageViewerPanel`, `StandardScanImageViewerPanel` and `StandardScanImageInfoPanel`.
"""
from typing import Tuple, Sequence, Dict
from collections import OrderedDict

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from dltscontrol.apptk import Panel
from dltscontrol.dlts import IScanImage

import math
import numpy as np

import tkinter as tk
import tkinter.ttk as ttk
import dltscontrol.tkext as tkext

import matplotlib.colors as mplc
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import skimage.util as skiu
import skimage.exposure as skie

# extension dependencies
from dltscontrol.app.core import rootLogger

logger = rootLogger.getChild(__name__)

class ImageViewerPanel(Panel):
    """ Panel which shows image data stored in a `numpy.ndarray`. Needs to be drawn and cleared manually by calling the appropriate methods."""

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def putImage(self, imageName: str, image: np.ndarray, imageSize: Tuple[int, int] = None, imagePosition: Tuple[int, int] = None):
        """ Inserts a new image with a name and optional additional image information. Doesn't necessarily refresh the panel, see `ImageViewerPanel.draw`. 
        
        Parameters
        ----------
        imageName: `str`:
            The name of the image.
        image: `numpy.ndarray`
            The image to display.
        imageSize: `Tuple[int, int]` (default: None)
            The size of the image. (Not the resolution but 'real world space'.)
        imagePosition: `Tuple[int, int]` (default: None)
            The 'real world position' of the top-left corner/origin of the image. 
        """
        raise NotImplementedError

    def draw(self):
        """ Draws the figure of the inserted images. """
        raise NotImplementedError

    def clear(self):
        """ Clears the drawn figure and clears all inserted images. """
        raise NotImplementedError

class ScanImageViewerPanel(Panel):
    """ Panel which shows depictable array data of `IScanImage`s. Needs to be drawn and cleared manually by calling the appropriate methods. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def setScanImages(self, scanImages: Sequence[IScanImage]):
        """ Sets the scan images of the panel. Doesn't necessarily refresh the panel, see `ScanImageViewerPanel.draw`. """
        raise NotImplementedError

    def draw(self):
        """ Draws the depictable data of the set scan image. """
        raise NotImplementedError

    def clear(self):
        """ Clears the drawn data and deletes the reference to the set scan image. """
        raise NotImplementedError

class ScanImageInfoPanel(Panel):
    """ Panel which shows informational data of `IScanImage`s mostly as text. """

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def setScanImages(self, scanImages: Sequence[IScanImage]):
        """ Sets the scan image of which the data has to be shown. Refreshes the panel automatically."""
        raise NotImplementedError

class StandardImageViewerPanel(ImageViewerPanel):
    """ `ImageViewerPanel` implementation based on the `matplotlib` package with a few basic image processing capabilities (Kept purpose of showing scan data in mind). """

    class ImageViewingError(Exception):
        """ Error during image viewing. """
        pass

    _VIEW_CONFIG_PADX = 2
    _VIEW_CONFIG_PADY = 2
    
    _TOOLBAR_CONFIG_PADX = 8
    _TOOLBAR_CONFIG_PADY = 1

    _ENTRY_PADX = 2

    _COLOR_MAP_NAMES = ('Purples', 'Blues', 'Greens', 'Oranges', 'Reds')
    _DEFAULT_COLOR_MAP_NAME = ('Greys')

    _DEFAULT_INTERPOLATION = "nearest"
    _BILINEAR_INTERPOLATION = "bilinear"

    _IMAGE_ORIGIN_LOWER = "lower"
    _IMAGE_ORIGIN_UPPER = "upper"

    _RGB_A_IMAGE_DIMENSION = 3
    _SCALAR_IMAGE_DIMENSION = 2
    
    _RGBA_PIXEL_DEPTH = 4
    _RGB_PIXEL_DEPTH = 3

    _DEFAULT_ALPHA_PERCENTAGE = 50

    _DEFAULT_START_INDEX = 1

    _DEFAULT_CONTRAST_LOW_PERCENTILE = 2
    _DEFAULT_CONTRAST_HIGH_PERCENTILE = 98

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)
        
        self._images = OrderedDict()
        self._imageNames = dict()
        self._axesExtents = dict()

        self._viewConfigVariables: Dict[str, tk.BooleanVar] = dict()
        self._viewConfigFrame = ttk.Frame(self.MainFrame)

        self._showAxesVariable = tk.BooleanVar(self.MainFrame, True)
        self._showTitlesVariable = tk.BooleanVar(self.MainFrame, True)
        self._invertVariable = tk.BooleanVar(self.MainFrame, False)
        self._interpolateVariable = tk.BooleanVar(self.MainFrame, False)
        self._mirrorYVariable = tk.BooleanVar(self.MainFrame, True)
        self._colorCycleVariable = tk.BooleanVar(self.MainFrame, False)
        self._colorCycleStartVariable = tkext.IntNoneVar(self.MainFrame, self._DEFAULT_START_INDEX)
        self._overlapVariable = tk.BooleanVar(self.MainFrame, False)
        self._overlapAlphaVariable = tkext.IntNoneVar(self.MainFrame, self._DEFAULT_ALPHA_PERCENTAGE)
        self._contrastStretchVariable = tk.BooleanVar(self.MainFrame, False)
        self._contrastStretchLowVariable = tkext.IntNoneVar(self.MainFrame, self._DEFAULT_CONTRAST_LOW_PERCENTILE)
        self._contrastStretchHighVariable = tkext.IntNoneVar(self.MainFrame, self._DEFAULT_CONTRAST_HIGH_PERCENTILE)

        self._colorCycleStartVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, self._onColorStartChange)
        self._overlapAlphaVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, self._onOverlapAlphaChange)
        self._contrastStretchLowVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, self._onConstrastLowChange)
        self._contrastStretchHighVariable.trace_add(tkext.TK_TRACE_MODE_WRITE, self._onConstrastHighChange)

        self._figure = Figure()

        self._canvas = FigureCanvasTkAgg(self._figure, master = self.MainFrame)
        self._canvas.draw()
        
        self._toolbar = NavigationToolbar2Tk(self._canvas, self.MainFrame)
        
        toolBarConfigFrame = ttk.Frame(self._toolbar)

        showTitlesFrame = ttk.Frame(toolBarConfigFrame)
        showTitleButton = ttk.Checkbutton(showTitlesFrame, text = "Show Titles", variable = self._showTitlesVariable, command = self.draw)

        showAxesFrame = ttk.Frame(toolBarConfigFrame)
        showAxesButton = ttk.Checkbutton(showAxesFrame, text = "Show Axes", variable = self._showAxesVariable, command = self.draw)

        invertFrame = ttk.Frame(toolBarConfigFrame)
        invertButton = ttk.Checkbutton(invertFrame, text = "Invert", variable = self._invertVariable, command = self.draw)

        interpolateFrame = ttk.Frame(toolBarConfigFrame)
        interpolateButton = ttk.Checkbutton(interpolateFrame, text = "Interpolate", variable = self._interpolateVariable, command = self.draw)

        mirrorYFrame = ttk.Frame(toolBarConfigFrame)
        mirrorYButton = ttk.Checkbutton(mirrorYFrame, text = "Mirror Y", variable = self._mirrorYVariable, command = self.draw)

        overlapFrame = ttk.Frame(toolBarConfigFrame)
        overlapButton = ttk.Checkbutton(overlapFrame, text = "Overlap - Alpha [%]:", variable = self._overlapVariable, command = self.draw)
        overlapAlphaEntry = tkext.IntEntry(toolBarConfigFrame, textvariable = self._overlapAlphaVariable, width = 5, maxValue = 100)

        colorCycleFrame = ttk.Frame(toolBarConfigFrame)
        colorCycleButton = ttk.Checkbutton(colorCycleFrame, text = "Color - Start Index:", variable = self._colorCycleVariable, command = self.draw)
        colorCycleStartEntry = tkext.IntEntry(toolBarConfigFrame, textvariable = self._colorCycleStartVariable, width = 5)

        contrastStretchFrame = ttk.Frame(toolBarConfigFrame)
        contrastStretchButton = ttk.Checkbutton(contrastStretchFrame, text = "Contrast Stretching [%]:", variable = self._contrastStretchVariable, command = self.draw)
        contrastStretchLowEntry = tkext.IntEntry(contrastStretchFrame, textvariable = self._contrastStretchLowVariable, width = 5, maxValue = 100)
        contrastStretchHighEntry = tkext.IntEntry(contrastStretchFrame, textvariable = self._contrastStretchHighVariable, width = 5, maxValue = 100)
        
        showTitleButton.pack(side = tk.LEFT)
        showAxesButton.pack(side = tk.LEFT)
        invertButton.pack(side = tk.LEFT)
        overlapButton.pack(side = tk.LEFT)
        # overlapAlphaEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)
        colorCycleButton.pack(side = tk.LEFT)
        # colorCycleStartEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)
        interpolateButton.pack(side = tk.LEFT)
        mirrorYButton.pack(side = tk.LEFT)
        contrastStretchButton.pack(side = tk.LEFT)
        contrastStretchLowEntry.pack(side = tk.LEFT, padx = self._ENTRY_PADX)
        contrastStretchHighEntry.pack(side = tk.LEFT)

        colorCycleFrame.grid(row = 0, column = 0, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        overlapFrame.grid(row = 1, column = 0, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)

        colorCycleStartEntry.grid(row = 0, column = 1, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        overlapAlphaEntry.grid(row = 1, column = 1, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)

        contrastStretchFrame.grid(row = 0, column = 2, columnspan = 3, padx = self._TOOLBAR_CONFIG_PADX, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)

        invertFrame.grid(row = 1, column = 2, padx = self._TOOLBAR_CONFIG_PADX, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        interpolateFrame.grid(row = 1, column = 3, padx = self._TOOLBAR_CONFIG_PADX, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        mirrorYFrame.grid(row = 1, column = 4, padx = self._TOOLBAR_CONFIG_PADX, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)

        showTitlesFrame.grid(row = 0, column = 5, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        showAxesFrame.grid(row = 1, column = 5, pady = self._TOOLBAR_CONFIG_PADY, sticky = tk.W)
        
        toolBarConfigFrame.pack(side = tk.LEFT, padx = self._TOOLBAR_CONFIG_PADX)

        self._viewConfigFrame.pack(side = tk.TOP, fill = tk.X, padx = self._VIEW_CONFIG_PADX)
        self._canvas.get_tk_widget().pack(side = tk.TOP, fill = tk.BOTH, expand = True)
        self._toolbar.update()

    @property
    def ShowTitles(self):
        """ If the image's names shall be shown. """
        return self._showTitlesVariable.get()

    @property
    def ShowAxes(self) -> bool:
        """ If the image's axes shall be shown. """
        return self._showAxesVariable.get()

    @property
    def Invert(self) -> bool:
        """ if the images shall be inverted. """
        return self._invertVariable.get()

    @property
    def Interpolate(self) -> bool:
        """ If the image data shall undergo an interpolation. """
        return self._interpolateVariable.get()

    @property
    def Interpolation(self) -> str:
        """ The interpolation algorithm to be passed to the image show method. """
        return self._BILINEAR_INTERPOLATION if self.Interpolate else self._DEFAULT_INTERPOLATION

    @property
    def MirrorY(self) -> bool:
        """ If the image shall be mirrored on the x-axis. """
        return self._mirrorYVariable.get()

    @property
    def Origin(self) -> str:
        """ Where the origin of the image is located. Whether upper (default) for 'top-left' or lower for 'bottom-left'. """
        return self._IMAGE_ORIGIN_LOWER if self.MirrorY else self._IMAGE_ORIGIN_UPPER 

    @property
    def DefaultColorMap(self) -> mplc.Colormap:
        """ The default color map for scalar images. """
        return cm.get_cmap(self._DEFAULT_COLOR_MAP_NAME).reversed()

    @property
    def ColorCycle(self) -> bool:
        """ If the scalar images shall be colored. """
        return self._colorCycleVariable.get() and self.ColorCycleStartIndex is not None

    @property
    def ColorCycleStartIndex(self) -> int:
        """ From where the scalar image coloring shall start. """
        return self._colorCycleStartVariable.get()

    @property
    def OverlapPlots(self) -> bool:
        """" If the images shall be drawn overlapped """
        return self._overlapVariable.get() and self.OverlapAlpha is not None

    @property
    def OverlapAlpha(self) -> int:
        """ The alpha the overlapped images shall be drawn with. """
        return self._overlapAlphaVariable.get()

    @property
    def ContrastStretch(self) -> bool:
        """ If the scalar image's contrast shall be stretched. """
        return self._contrastStretchVariable.get() and self.ContrastStretchLow is not None and self.ContrastStretchHigh is not None \
            and self.ContrastStretchLow < self.ContrastStretchHigh

    @property
    def ContrastStretchLow(self) -> int:
        """ The lower percentile from to start contrast stretching. """
        return self._contrastStretchLowVariable.get()

    @property
    def ContrastStretchHigh(self) -> int:
        """ The higher percentile from where to start contrast stretching. """
        return self._contrastStretchHighVariable.get()

    def _onColorStartChange(self, name, index, mode):
        """ Called when color start index variable changes. """
        if self.ColorCycle:
            self.draw()

    def _onOverlapAlphaChange(self, name, index, mode):
        """ Called when overlap alpha variable changes. """
        if self.OverlapAlpha:
            self.draw()

    def _onConstrastLowChange(self, name, index, mode):
        """ Called when contrast stretching's lower percentile variable changes. """
        if self.ContrastStretch:
            self.draw()

    def _onConstrastHighChange(self, name, index, mode):
        """ Called when contrast stretching's higher percentile variable changes. """
        if self.ContrastStretch:
            self.draw()

    def _onViewSelectionChanged(self):
        """ Called when the selection of images to show changes. (Checkbutton bar) """
        self.draw()

    def _refreshCheckButtons(self):
        """ Creates a bar with check buttons to let the user decide which inserted images shall be drawn. """
        self._viewConfigVariables.clear()

        for child in self._viewConfigFrame.winfo_children():
            child.destroy()

        checkButtons = list()

        for imageId in self._images:
            imageName = self._imageNames[imageId]
            variable = tk.BooleanVar(self._viewConfigFrame, True)
            checkButtons.append(ttk.Checkbutton(self._viewConfigFrame, text = imageName, variable = variable, command = self._onViewSelectionChanged))

            self._viewConfigVariables[imageId] = variable
        
        for checkButton in checkButtons:
            checkButton.pack(side = tk.LEFT, padx = self._VIEW_CONFIG_PADX, pady = self._VIEW_CONFIG_PADY)

    def putImage(self, imageName: str, image: np.ndarray, imageSize: Tuple[int, int] = None, imagePosition: Tuple[int, int] = None):
        imageId = id(image)
        
        # check image data type 
        if not np.issubdtype(image.dtype, np.floating) and not np.issubdtype(image.dtype, np.integer):
            raise self.ImageViewingError("Can't show scalar image which isn't of any `numpy.floating` or `numpy.integer` type.")
        
        # check image shape
        if len(image.shape) == self._RGB_A_IMAGE_DIMENSION:
            if image.shape[-1] < self._RGB_PIXEL_DEPTH or image.shape[-1] > self._RGBA_PIXEL_DEPTH:
                raise self.ImageViewingError("Can't show image with pixel depth '{0}'.".format(image.shape[-1]))
            
            # unify rgb/rgba image data type to 'unsigned' float
            image = skiu.img_as_float(skiu.img_as_uint(image))

            if image.shape[-1] == self._RGB_PIXEL_DEPTH: 
                # convert rgb to rgba image 
                newImage = np.ones(image.shape[:-1] + (self._RGBA_PIXEL_DEPTH, ), image.dtype)
                newImage[..., :image.shape[-1]] = image

                image = newImage
        elif len(image.shape) == self._SCALAR_IMAGE_DIMENSION:      
            # normalize scalar images
            image = mplc.Normalize()(image)
        else:
            raise self.ImageViewingError("Can't show image of dimension '{0}'.".format(len(image.shape)))
       
        self._images[imageId] = image
        self._imageNames[imageId] = imageName

        # set axes if provided
        if imageSize:
            position = imagePosition if imagePosition else (0, 0)
            self._axesExtents[imageId] = (position[0], position[0] + imageSize[0], position[1] + imageSize[1], position[1])

        self._refreshCheckButtons()

    def draw(self):
        self._figure.clear()

        # determine which images to draw
        visibleImageIds = tuple(filter(lambda imageId: self._viewConfigVariables[imageId].get(), self._images))

        rows = 1 
        columns = 1

        if not self.OverlapPlots and visibleImageIds:
            # create a 'good looking' image grid
            rows = int(len(visibleImageIds) ** 0.5)
            columns = math.ceil(len(visibleImageIds) / rows)

        for imageIndex, imageId in enumerate(visibleImageIds):
            # draw each single image and apply selected effects

            image = np.copy(self._images[imageId])
            imageName = self._imageNames[imageId]
            
            if len(image.shape) == self._SCALAR_IMAGE_DIMENSION:
                # apply effects only supported on scalar images

                if self.ContrastStretch:
                    percentileLow = np.percentile(image, self.ContrastStretchLow)
                    percentileHigh = np.percentile(image, self.ContrastStretchHigh)
                    image = skie.rescale_intensity(image, in_range = (percentileLow, percentileHigh))

                colorMap: mplc.Colormap = self.DefaultColorMap

                if self.ColorCycle and imageIndex >= self.ColorCycleStartIndex: 
                    colorMap: mplc.Colormap = cm.get_cmap(self._COLOR_MAP_NAMES[imageIndex % len(self._COLOR_MAP_NAMES)]).reversed()     

                image = colorMap(image)

            # if self.ColorCycle:
            #     sliceMask = list()
            #     if imageIndex >= self.ColorCycleStartIndex:
            #         dataMaskMod = format(1 + imageIndex - self.ColorCycleStartIndex, '03b')[:-4:-1]
            #         for sliceIndex in range(len(dataMaskMod)):
            #             if int(dataMaskMod[sliceIndex]):
            #                 sliceMask.append(sliceIndex)                        
            #         image[:, :, sliceMask] = 0
                    
            if self.Invert:
                # don't invert the alpha channel
                image[..., :-1] = skiu.invert(image[..., :-1])
            
            # only one subplot if the image shall be overlapped
            if not self.OverlapPlots or imageIndex == 0:
                plot = self._figure.add_subplot(rows, columns, imageIndex + 1)
            else:
                image[:, :, -1] = self.OverlapAlpha / 100
            
            # combine image names to one title if they shall be overlapped
            if self.ShowTitles:
                if not self.OverlapPlots or imageIndex == 0:
                    plot.set_title(imageName)
                else:
                    plot.set_title(plot.get_title() + " + " + imageName)
            
            if not self.ShowAxes:
                plot.set_axis_off()
            
            # show the image finally
            if imageId in self._axesExtents.keys():
                extent = self._axesExtents[imageId]

                # swap bounds if mirror is on
                if self.MirrorY:
                    extent = list(extent)
                    extent[-1], extent[-2] = extent[-2], extent[-1]

                plot.imshow(image, origin = self.Origin, interpolation = self.Interpolation, extent = extent)
            else:
                plot.imshow(image, origin = self.Origin, interpolation = self.Interpolation)

        self._canvas.draw()

    def clear(self):
        self._images.clear()
        self._imageNames.clear()
        self._axesExtents.clear()
        self._figure.clear()
        self._refreshCheckButtons()      

class StandardScanImageViewerPanel(ScanImageViewerPanel):
    """ Default `ScanImageViewerPanel` implementation which uses an `ImageViewerPanel` to show the scan image's data images. """

    _MAX_IMAGE_ARRAY_SHAPE_LENGTH = 3

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

        self._imageViewerPanel = self.createPanel(ImageViewerPanel, self.getTk())
        self._imageViewerPanel.MainFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)

    def setScanImages(self, scanImages: Sequence[IScanImage]):
        self._imageViewerPanel.clear()

        if scanImages:
            for scanImage in scanImages:
                try:
                    self._imageViewerPanel.putImage(scanImage.getName(), scanImage.getImageArray(), scanImage.getSize(), scanImage.getPosition())
                except Exception as ex:
                    logger.exception(ex)
    
    def draw(self):
        self._imageViewerPanel.draw()

    def clear(self):
        self._imageViewerPanel.clear()

class StandardScanImageInfoPanel(ScanImageInfoPanel):
    """ Default `ScanImageInfoPanel` implementation. """

    _GRID_PADX = 6
    _GRID_PADY = 6

    _FRAME_PADX = 2
    _FRAME_PADY = 2

    _NAME_TEMPLATE = "{0}"
    _DATE_TEMPLATE = "Date\n{0}"
    _DURATION_TEMPLATE = "Duration\n{0}"
    _COMPLETION_TEMPLATE = "Completion\n{:.1%}"
    _POSITION_TEMPLATE = "Position (x, y, z, xt)\n{0}"
    _SIZE_TEMPLATE = "Size\n{0}"
    _RESOLUTION_TEMPLATE = "Resolution\n{0}"
    _LASER_INTENSITY_TEMPLATE = "Laser Intensity\n{0}"
    _DATA_SHAPE_TEMPLATE = "Data Shape\n{0}"
    _DATA_STATISTICS_TEMPLATE = "Data (Min, Max, Average, Median)\n({:.5g}, {:.5g}, {:.5g}, {:.5g})"

    def __init__(self, tkMaster, context, componentContext):
        super().__init__(tkMaster, context, componentContext)

    def setScanImages(self, scanImages: Sequence[IScanImage]):
        for child in self.MainFrame.winfo_children():
            child.destroy()

        if scanImages:
            for index, scanImage in enumerate(scanImages):
                name = scanImage.getName()
                date = scanImage.getScanDate()
                duration = scanImage.getScanDuration()
                position = scanImage.getPosition() + (scanImage.getZPosition(), scanImage.getXTilt())

                dateString = self._DATE_TEMPLATE.format(date.strftime("%x %X")) if date is not None else "None"

                if duration is not None:
                    hours = int(duration.seconds / 3600)
                    minutes = int(duration.seconds / 60 % 60)
                    seconds = int(duration.seconds % 60)
                    
                    durationString = self._DURATION_TEMPLATE.format("{:02d}:{:02d}:{:02d}:{:02d}".format(duration.days, hours, minutes, seconds))
                else:
                    durationString = "None"

                imageArray = scanImage.getImageArray()
                shape = imageArray.shape
                min = np.min(imageArray)
                max = np.max(imageArray)
                avg = np.mean(imageArray)
                med = np.median(imageArray)

                if index > 0:
                    ttk.Separator(self.MainFrame).pack(side = tk.TOP, fill = tk.X, pady = self._FRAME_PADY)

                scanImageFrame = ttk.Frame(self.MainFrame)

                nameLabel = ttk.Label(scanImageFrame, text = self._NAME_TEMPLATE.format(name), justify = tk.CENTER)
                dateLabel = ttk.Label(scanImageFrame, text = dateString, justify = tk.CENTER)
                durationLabel = ttk.Label(scanImageFrame, text = durationString, justify = tk.CENTER)
                completionLabel = ttk.Label(scanImageFrame, text = self._COMPLETION_TEMPLATE.format(scanImage.getCompletion()), justify = tk.CENTER)
                positionLabel = ttk.Label(scanImageFrame, text = self._POSITION_TEMPLATE.format(position), justify = tk.CENTER)
                sizeLabel = ttk.Label(scanImageFrame, text = self._SIZE_TEMPLATE.format(scanImage.getSize()), justify = tk.CENTER)
                resolutionLabel = ttk.Label(scanImageFrame, text = self._RESOLUTION_TEMPLATE.format(scanImage.getResolution()), justify = tk.CENTER)
                laserIntensityLabel = ttk.Label(scanImageFrame, text = self._LASER_INTENSITY_TEMPLATE.format(scanImage.getLaserIntensity()), justify = tk.CENTER)
                dataShapeLabel = ttk.Label(scanImageFrame, text = self._DATA_SHAPE_TEMPLATE.format(shape), justify = tk.CENTER)
                dataStatisticsLabel = ttk.Label(scanImageFrame, text = self._DATA_STATISTICS_TEMPLATE.format(min, max, avg, med), justify = tk.CENTER)

                nameLabel.grid(row = 0, column = 0, columnspan = 9, padx = self._GRID_PADX, pady = self._GRID_PADY)

                dateLabel.grid(row = 1, column = 0, padx = self._GRID_PADX, pady = self._GRID_PADY)
                durationLabel.grid(row = 1, column = 1, padx = self._GRID_PADX, pady = self._GRID_PADY)
                completionLabel.grid(row = 1, column = 2, padx = self._GRID_PADX, pady = self._GRID_PADY)
                positionLabel.grid(row = 1, column = 3, padx = self._GRID_PADX, pady = self._GRID_PADY)
                sizeLabel.grid(row = 1, column = 4, padx = self._GRID_PADX, pady = self._GRID_PADY)
                resolutionLabel.grid(row = 1, column = 5, padx = self._GRID_PADX, pady = self._GRID_PADY)
                laserIntensityLabel.grid(row = 1, column = 6, padx = self._GRID_PADX, pady = self._GRID_PADY)
                dataShapeLabel.grid(row = 1, column = 7, padx = self._GRID_PADX, pady = self._GRID_PADY)
                dataStatisticsLabel.grid(row = 1, column = 8, padx = self._GRID_PADX, pady = self._GRID_PADY)

                scanImageFrame.pack(side = tk.TOP, padx = self._FRAME_PADX, pady = self._FRAME_PADY)
        else:
            ttk.Label(self.MainFrame, text = "No Scan Data", justify = tk.CENTER).pack(fill = tk.BOTH, expand = True)

# extension area

from dltscontrol.app.manifest import manifest

# panels
manifest.insert(StandardImageViewerPanel)
manifest.insert(StandardScanImageInfoPanel)
manifest.insert(StandardScanImageViewerPanel)