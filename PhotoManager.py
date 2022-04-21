from tkinter import *
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance
from PIL import *
import os

#
# This class defines the main GUI and fuctionality of Bittu's Photo Manager.
#
class PhotoManagerGUI:
    
    # Image size to display.
    imgSize = (810, 540)
    rotateSize = (390, 360)
    thumbSize = (128, 128)

    # List of image file path names and current image file index.
    imgPathList = []
    currImgIdx = -1

    # Image file extension supported.
    imgType = ['jpg', 'png', 'bmp', 'gif']

    # Current Image object Stack on Display. Last saved image for 'Save As' operation. Current Image object
    # for 'Undo' and 'Redo' Operations.
    currImgObjStack = []
    lastSavedImg = Image.new('RGB', imgSize)
    currenImgObj = Image.new('RGB', imgSize)

    # Enhance Image List.
    enhanceImgList = []

    # scale values dictionary.
    scaleValues = {
        'color': 1.0,
        'contrast': 1.0,
        'brightness': 1.0,
        'sharpness': 1.0,
    }

    def __init__(self, master):
        
        # Get the master.
        self.master = master

        # Putting Additional Style.
        self.bgcolor = 'black'
        self.fgcolor = '#e13352'
        self.font = ('Areal', 11, 'bold')

        self.master.title('Bittu\'s Image Browser & Manager')
        self.master.geometry('850x600+200+50')
        self.master.resizable(False,False)
        self.master.configure(background = self.bgcolor)

        self.style = ttk.Style()
        self.style.configure('TButton', font = self.font, foreground = self.fgcolor)
        self.style.configure('TFrame', background = self.bgcolor)
        self.style.configure('TLabel', background = self.bgcolor, font = self.font, foreground = self.fgcolor)
        self.style.configure('TScale', background = self.bgcolor)

        # Creating Menubar.
        self.master.option_add('*tearOff', False)
        self.menuBar = Menu(self.master)
        self.master.config(menu = self.menuBar)
        
        # Creating the Menu.
        self.file = Menu(self.menuBar)
        self.edit = Menu(self.menuBar)

        self.menuBar.add_cascade(menu = self.file, label = 'File')
        self.menuBar.add_cascade(menu = self.edit, label = 'Edit')

        # Creating File menu items.
        self.file.add_command(label = 'Open Pic', command = self.openPic)
        self.file.add_command(label = 'Open Folder', command = self.openPicFolder)
        
        # Add Line separator.
        self.file.add_separator()

        # Creating File menu items.
        self.file.add_command(label = 'Save', command = self.saveImg)
        self.file.add_command(label = 'Save As', command = self.saveAsImg)

        # Creating Edit menu items.
        self.edit.add_command(label = 'Undo <<-', command = self.revertImg)
        self.edit.add_command(label = 'Redo ->>', command = self.redoImg)

        # Add Line separator.
        self.edit.add_separator()
        
        # Add Other Image Edit options.
        self.edit.add_command(label = 'Crop', command = self.corpImg)
        self.edit.add_command(label = 'Rotate', command = self.rotateImg)
        self.edit.add_command(label = 'Enhance Picture', command = self.makeEnhance)
        
        # Add Line separator.
        self.edit.add_separator()

        self.edit.add_command(label = 'Old Style', command = self.makeBWImg)
        self.edit.add_command(label = 'Thumbnail', command = self.makeThumbnail)
        self.edit.add_command(label = 'Super-Impose', command = self.makeImpose)
        
        # Disable the Edit functions initially.
        self.edit.entryconfig('Undo <<-', state = DISABLED)
        self.edit.entryconfig('Redo ->>', state = DISABLED)
        self.edit.entryconfig('Crop', state = DISABLED)
        self.edit.entryconfig('Rotate', state = DISABLED)
        self.edit.entryconfig('Enhance Picture', state = DISABLED)
        self.edit.entryconfig('Old Style', state = DISABLED)
        self.edit.entryconfig('Thumbnail', state = DISABLED)
        self.edit.entryconfig('Super-Impose', state = DISABLED)

        # Creating frames
        self.displayFrame = ttk.Frame(self.master)
        self.buttonFrame = ttk.Frame(self.master)

        # Geometry Manager Method.
        self.displayFrame.pack()
        self.buttonFrame.pack()

        # Creating Canvas.
        self.disCanvas = Canvas(self.displayFrame, bg="white", width= 810, height = 540, cursor = 'cross')
        self.disCanvas.pack(pady = 5)

        # Co-ordinate variables and crop area.
        self.startX = None
        self.startY = None
        self.finalX = None
        self.finalY = None
        self.cropArea = None

        # Bind the mouse event listener methods for the Canvas.
        self.disCanvas.bind("<ButtonPress-1>", self.startCropArea)
        self.disCanvas.bind("<B1-Motion>", self.drawCropArea)
        self.disCanvas.bind("<ButtonRelease-1>", self.enableCrop)

        # Creating Prev and Next Buttons.
        self.prevButton = ttk.Button(self.buttonFrame, text = '<<Prev', command = self.showPrevImg)
        self.nextButton = ttk.Button(self.buttonFrame, text = 'Next>>', command = self.showNextImg)

        # Geometry Manager Method.
        self.prevButton.grid(row = 0, column = 0, padx = 10, pady = 5, sticky = 'nw')
        self.nextButton.grid(row = 0, column = 1, padx = 10, pady = 5, sticky = 'ne')

        # Button initial state - Disable.
        self.prevButton.config(state = DISABLED)
        self.nextButton.config(state = DISABLED)
    #
    # This method enables most of the edit functionalities
    #
    def enableEditCommand(self):
        self.edit.entryconfig('Rotate', state = NORMAL)
        self.edit.entryconfig('Enhance Picture', state = NORMAL)
        self.edit.entryconfig('Old Style', state = NORMAL)
        self.edit.entryconfig('Thumbnail', state = NORMAL)
        self.edit.entryconfig('Super-Impose', state = NORMAL)
    
    #
    # This method takes image file path or image object as argument and shows the image in the canvas.
    #
    def showImg(self, imgPath = None, imgObj = None, imgChg = False):
        
        # Open the image file from the path or image object and resize the image.
        if imgPath:
            self.rawImg = Image.open(imgPath)
        elif imgObj:
            self.rawImg = imgObj
        else:
            # If the method called with no argument, show the empty canvas.
            self.disCanvas.config(bg = 'white')
            return None

        # Put current image object into the Stack for future reference.
        if imgChg or len(PhotoManagerGUI.currImgObjStack) == 0:
            PhotoManagerGUI.currImgObjStack.append(self.rawImg)

        # If atleast there is more than one image to revert, enable the 'Undo' Button.
        if len(PhotoManagerGUI.currImgObjStack) > 1:
            self.edit.entryconfig('Undo <<-', state = NORMAL)
        
        # If the image is not thumbnail, then resize the image.
        if self.rawImg.size[0] >= PhotoManagerGUI.imgSize[0] \
        and self.rawImg.size[1] >= PhotoManagerGUI.imgSize[1]:
            self.imgResized = self.rawImg.resize(PhotoManagerGUI.imgSize)
        else:
            self.imgResized = self.rawImg                

        # Create the PhotoImage.
        self.photo = ImageTk.PhotoImage(image = self.imgResized)

        # Show the image in Canvas.
        if self.imgResized.size[0] >= PhotoManagerGUI.imgSize[0] \
        and self.imgResized.size[1] >= PhotoManagerGUI.imgSize[1]:
            self.disCanvas.create_image(0, 0, image = self.photo, anchor = NW)
        else:
            self.startPosX = ((PhotoManagerGUI.imgSize[0] // 2) - (self.imgResized.size[0] // 2))
            self.startPosY = ((PhotoManagerGUI.imgSize[1] // 2) - (self.imgResized.size[1] // 2))
            
            if self.startPosX < 0:
                self.startPosX = 0

            if self.startPosY < 0:
                self.startPosY = 0
                
            self.disCanvas.create_image(self.startPosX, self.startPosY, image = self.photo, anchor = NW)

    #
    # This Method set initial values to image file list, current image index and image directory values.
    #
    def initImgVar(self):
        PhotoManagerGUI.imgPathList = []
        PhotoManagerGUI.currImgIdx = -1
        PhotoManagerGUI.currImgObjStack = []
        PhotoManagerGUI.lastSavedImg = Image.new('RGB', PhotoManagerGUI.imgSize)
        PhotoManagerGUI.currenImgObj = Image.new('RGB', PhotoManagerGUI.imgSize)

    #
    # This method open a picture file from file directory using file dialog prompt 
    # and shows the image in the canvas.
    #
    def openPic(self):
        # Initialize image directory path and image file List.
        self.initImgVar()

        # Get the path of the image file.
        self.imgPath = filedialog.askopenfile(mode='r', title = 'Open a Picture', 
                                              filetypes = (('JPG File', '*.jpg'),('PNG File', '*.png'),
                                                           ('Bitmap File', '*.bmp'), ('GIF File', '*.gif')))
        if self.imgPath:
            # Store the image path into the path list for future use.
            PhotoManagerGUI.currImgIdx += 1
            PhotoManagerGUI.imgPathList.append(self.imgPath.name)

            # Show the image with image full path
            self.showImg(imgPath = self.imgPath.name)

            # Enable Image edit functionalities.
            self.enableEditCommand()
 
    #
    # This method open the folder and get the list of picture file in it. 
    # It shows the first picture in the list into the canvas.
    #
    def openPicFolder(self):
        # Initialize image directory path and image file List.
        self.initImgVar()

        # Get the folder path.
        self.folderPath = filedialog.askdirectory(title = 'Open a Picture Folder')
        if self.folderPath:
            PhotoManagerGUI.imgDir = self.folderPath

            # Iterrate through the directory content and if it is image file with pre-defiened file types
            # then append into the list of image file.

            for self.imgFile in os.listdir(self.folderPath):
                self.imgExt = self.getFileExtension(self.imgFile)
                if self.imgExt in PhotoManagerGUI.imgType:
                    self.imagePath = self.folderPath + '/' + self.imgFile
                    PhotoManagerGUI.imgPathList.append(self.imagePath)

            # Show the image from the list of image file.
            self.showNextImg()

            # Enable the 'Next' Button.
            self.nextButton.config(state = NORMAL)

            # Enable Image edit functionalities.
            self.enableEditCommand()

            # Bind the Left and Right arrow events.
            self.master.bind("<Left>", self.leftImg)
            self.master.bind("<Right>", self.rightImg)

    #
    # This function gets extension/type of the given file
    #
    def getFileExtension(self, SourceFile):
        self.FileNameSplit = SourceFile.split(".")
        self.FileExtention = self.FileNameSplit[-1].lower()
        return self.FileExtention
    
    #
    # Left arrow key event handler.
    #
    def leftImg(self, event):
        # If the current image is the first in the list, then then generate error.
        if PhotoManagerGUI.currImgIdx == 0:
            messagebox.showerror(title = 'Error', message = 'No previous picture!')
        else:
            self.showPrevImg()
    
    #
    # Right arrow key event handler.
    #
    def rightImg(self, event):
        # If the current image is the last image of the list, then generate error.
        if PhotoManagerGUI.currImgIdx == (len(PhotoManagerGUI.imgPathList) - 1):
            messagebox.showerror(title = 'Error', message = 'No next picture!')
        else:
            self.showNextImg()

    #
    # This method gets the next image from the list and show it to canvas.
    #
    def showNextImg(self):
        # Makes the current image object stack empty.
        PhotoManagerGUI.currImgObjStack = []

        # Show the next image.
        PhotoManagerGUI.currImgIdx += 1
        self.FullImgPath = PhotoManagerGUI.imgPathList[PhotoManagerGUI.currImgIdx]
        self.showImg(imgPath = self.FullImgPath)
        
        # If the current image not the first image in the list, then enable the 'Prev' Button.
        if PhotoManagerGUI.currImgIdx > 0:
            self.prevButton.config(state = NORMAL)

        # If the current image is the last image of the list, then disable the 'Next' Button.
        if PhotoManagerGUI.currImgIdx == (len(PhotoManagerGUI.imgPathList) - 1):
            self.nextButton.config(state = DISABLED)
    
    #
    # This method gets the previous image from the list and show it to canvas.
    #
    def showPrevImg(self):
        # Makes the current image object stack empty.
        PhotoManagerGUI.currImgObjStack = []

        # Show the previous image.
        PhotoManagerGUI.currImgIdx -= 1
        self.FullImgPath = PhotoManagerGUI.imgPathList[PhotoManagerGUI.currImgIdx]
        self.showImg(imgPath = self.FullImgPath)

        # If the current image is not the last image in the list, then enable the 'Next' Button.
        if PhotoManagerGUI.currImgIdx < (len(PhotoManagerGUI.imgPathList) - 1):
            self.nextButton.config(state = NORMAL)
        
        # If the current image is the first in the list, then disable the 'Prev' Button.
        if PhotoManagerGUI.currImgIdx == 0:
            self.prevButton.config(state = DISABLED)

    #
    # This method saves the current image with the same name
    #
    def saveImg(self):
        # Get the current image object from the stack.
        try:
            self.finalImg = PhotoManagerGUI.currImgObjStack.pop()
            PhotoManagerGUI.lastSavedImg = self.finalImg
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Image Already Saved!')
        else:
            # Makes the current image object stack empty.
            PhotoManagerGUI.currImgObjStack = []

            # Get the current image path and save the image object in same path.
            self.FullImgPath = PhotoManagerGUI.imgPathList[PhotoManagerGUI.currImgIdx]
            self.finalImg.save(self.FullImgPath)    

    #
    # This method 'Save AS' the current image with the user provided name.
    #
    def saveAsImg(self):
        # Get the current image object from the stack.
        try:
            self.finalImg = PhotoManagerGUI.currImgObjStack.pop()
            PhotoManagerGUI.lastSavedImg = self.finalImg

            # Makes the current image object stack empty.
            PhotoManagerGUI.currImgObjStack = []
        except IndexError:
            pass
        finally:
            # Get the current image path from the user and save the image with that name.
            self.FullImgPath = filedialog.asksaveasfile(mode='w', defaultextension = '*.jpg', filetypes = (('JPG File', '*.jpg'),('All File', '*')))
            PhotoManagerGUI.lastSavedImg.save(self.FullImgPath)
        
    #
    #  This method takes the currently showing image and converts it into Black and White.
    #              
    def makeBWImg(self):
        # Get the current image object from the stack.
        try:
            self.inputImg = PhotoManagerGUI.currImgObjStack[-1]
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # Convert the image into Black and White and show the image.
            self.outputImg = self.inputImg.convert(mode = 'L')
            self.showImg(imgObj = self.outputImg, imgChg = True)

    #
    #  This method takes the currently showing image and converts it into Thumbnail image.
    #              
    def makeThumbnail(self):
        # Get the current image object from the stack.
        try:
            self.outputImg =  PhotoManagerGUI.currImgObjStack[-1].copy()
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # Convert the image into Thumbnail image and show the image.
            self.outputImg.thumbnail(PhotoManagerGUI.thumbSize)
            self.showImg(imgObj = self.outputImg, imgChg = True)
    
    #
    #  This method takes the currently showing image and rotates the image.
    #              
    def rotateImg(self):
        # Get the current image object from the stack.
        try:
            self.inputImg = PhotoManagerGUI.currImgObjStack[-1]
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # Rotates the image 90 degree and resize the image.
            self.outputImg = self.inputImg.rotate(angle = 90, expand = True)
            self.showImg(imgObj = self.outputImg, imgChg = True)
        
    #
    # This method make super impose the current image with another image.
    #
    def makeImpose(self):
        # Get the current image object from the stack.
        try:
            self.inputImg1 = PhotoManagerGUI.currImgObjStack[-1]
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # Get another image from the file.
            self.inputPath2 = filedialog.askopenfile(mode='r', title = 'Open a Picture', 
                              filetypes = (('JPG File', '*.jpg'),('PNG File', '*.png'),
                                          ('Bitmap File', '*.bmp'), ('GIF File', '*.gif')))
            
            if self.inputPath2:
                # Make the second image same as first image.
                self.inputImg2 = Image.open(self.inputPath2.name).resize(self.inputImg1.size).convert(mode = self.inputImg1.mode)
                
                # Super-impose the current image with another image and display.
                self.outputImg = Image.blend(self.inputImg1, self.inputImg2, 0.5)
                self.showImg(imgObj = self.outputImg, imgChg = True)

    #
    # This method revert back the changes made on the currently showing image.
    #
    def revertImg(self):
        # Get the current image objects from the stack.
        try:
            PhotoManagerGUI.currenImgObj = PhotoManagerGUI.currImgObjStack.pop()
            self.tempImg = PhotoManagerGUI.currImgObjStack.pop()
        except IndexError:
            self.edit.entryconfig('Undo <<-', state = DISABLED)
        else:
            if len(PhotoManagerGUI.currImgObjStack) == 0:
                self.edit.entryconfig('Undo <<-', state = DISABLED)

            self.edit.entryconfig('Redo ->>', state = NORMAL)
            self.showImg(imgObj = self.tempImg, imgChg = True)

    #
    # This method apply back the changes made on the currently showing image. ('Redo' operation)
    #
    def redoImg(self):
        # Show the previously saved image.        
        self.tempImg = PhotoManagerGUI.currenImgObj
        self.showImg(imgObj = self.tempImg, imgChg = True)
        self.edit.entryconfig('Redo ->>', state = DISABLED)
    
    #
    #  This method enhances the Color, Brightness, Contrast, Sharpness of the current image.
    #              
    def makeEnhance(self):
        # Get the current image object from the stack.
        try:
            self.inputImg = PhotoManagerGUI.currImgObjStack[-1]
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # Create a top-level window to hold all the image enhance sliders.
            self.createEnhanceSliders(self.inputImg)
    
    def createEnhanceSliders(self, imageInp):
        # Create a Top-level Window and lift the window.
        self.sliderWindow = Toplevel(self.master)
        self.sliderWindow.lift(self.master)

        # Putting style and size of top-level window.
        self.sliderWindow.title('Image Enhancer')
        self.sliderWindow.geometry('350x200+700+100')
        self.sliderWindow.configure(background = self.bgcolor)

        # Pushing the input image to the enhance image stack.
        PhotoManagerGUI.enhanceImgList.append(imageInp)

        # Creating Frames.
        self.controlFrame = ttk.Frame(self.sliderWindow)
        self.pressFrame = ttk.Frame(self.sliderWindow)

        # Geometry Manager Method.
        self.controlFrame.pack()
        self.pressFrame.pack()

        # Creating Labels on the slider window.
        ttk.Label(self.controlFrame, text = 'Color').grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nw')
        ttk.Label(self.controlFrame, text = 'Contrast').grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'nw')
        ttk.Label(self.controlFrame, text = 'Brightness').grid(row = 2, column = 0, padx = 5, pady = 5, sticky = 'nw')
        ttk.Label(self.controlFrame, text = 'Sharpness').grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'nw')

        # Creatinge Scales on the slider window.
        self.colorScale = ttk.Scale(self.controlFrame, from_ = 0, to = 200, length = 200, orient = HORIZONTAL)
        self.contrastScale = ttk.Scale(self.controlFrame, from_ = 0, to = 200, length = 200, orient = HORIZONTAL)
        self.brightScale = ttk.Scale(self.controlFrame, from_ = 0, to = 200, length = 200, orient = HORIZONTAL)
        self.sharpScale = ttk.Scale(self.controlFrame, from_ = 0, to = 200, length = 200, orient = HORIZONTAL)

        # Set the initial values of the Scales to 100.
        self.setInitialValues()

        # Attached listener methods to the Scales that is invokes when the scale values change.
        self.colorScale.bind("<ButtonRelease-1>", self.enhanceImageColor)
        self.contrastScale.bind("<ButtonRelease-1>", self.enhanceImageContrast)
        self.brightScale.bind("<ButtonRelease-1>", self.enhanceImageBrightness)
        self.sharpScale.bind("<ButtonRelease-1>", self.enhanceImageSharpness)
        
        # Geometry Manager Method.
        self.colorScale.grid(row = 0, column = 1, padx = 5, pady = 5, sticky = 'ne')            
        self.contrastScale.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'ne')
        self.brightScale.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'ne')
        self.sharpScale.grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'ne')

        # Creating the Button.
        ttk.Button(self.pressFrame, text = 'Done',
                   command = self.finishEnhance).grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'ne')
        ttk.Button(self.pressFrame, text = 'Reset',
                   command = self.resetEnhance).grid(row = 0, column = 1, padx = 5, pady = 5, sticky = 'ne')
        ttk.Button(self.pressFrame, text = 'Cancel',
                   command = self.clearEnhance).grid(row = 0, column = 2, padx = 5, pady = 5, sticky = 'ne')
      
    def setInitialValues(self):
        # Set the initial values to 100%.
        self.colorScale.set(100)
        self.contrastScale.set(100)
        self.brightScale.set(100)
        self.sharpScale.set(100)
        
    #
    # This method enhances image.
    #
    def enhanceImg(self):
        # Get the input image.
        self.image = PhotoManagerGUI.enhanceImgList[0]

        # Color Enhance.
        self.colorEnhance = ImageEnhance.Color(self.image)
        self.tempImg1 = self.colorEnhance.enhance(factor = PhotoManagerGUI.scaleValues['color'])

        # Contrast Enhance.
        self.contrastEnhance = ImageEnhance.Contrast(self.tempImg1)
        self.tempImg2 = self.contrastEnhance.enhance(factor = PhotoManagerGUI.scaleValues['contrast'])

        # Brightness Enhance.
        self.brightEnhance = ImageEnhance.Brightness(self.tempImg2)
        self.tempImg3 = self.brightEnhance.enhance(factor = PhotoManagerGUI.scaleValues['brightness'])

        # Sharpness Enhance.
        self.sharpEnhance = ImageEnhance.Sharpness(self.tempImg3)
        self.tempImg4 = self.sharpEnhance.enhance(factor = PhotoManagerGUI.scaleValues['sharpness'])     

        # Put the image into enhance image list.
        PhotoManagerGUI.enhanceImgList.append(self.tempImg4)

        # Return the final image object.
        return self.tempImg4    

    #
    # This method enhances the Color when the scale is changed.
    #             
    def enhanceImageColor(self, event):
        # Get the scale value.
        self.scaleVal = self.colorScale.get()

        # Enhances the image based on scale value.
        self.colorFactor = round(float(self.scaleVal) / 100, 1)

        # Store the color factor into the scaleValues dictionary.
        PhotoManagerGUI.scaleValues['color'] = self.colorFactor

        # Enhance Image:
        self.outImg = self.enhanceImg()

        # Show the enhanced image.
        self.showImg(imgObj = self.outImg)

    #
    # This method enhances the Contrast when the scale is changed.
    #             
    def enhanceImageContrast(self, event):
        # Get the scale value.
        self.scaleVal = self.contrastScale.get()
        
        # Enhances the image based on scale value.
        self.contrastFactor = round(float(self.scaleVal) / 100, 1)

        # Store the contrast factor into the scaleValues dictionary.
        PhotoManagerGUI.scaleValues['contrast'] = self.contrastFactor

        # Enhance Image:
        self.outImg = self.enhanceImg()       
 
        # Show the enhanced image.
        self.showImg(imgObj = self.outImg)

    #
    # This method enhances the Brightness when the scale is changed.
    #             
    def enhanceImageBrightness(self, event):
        # Get the input image.
        self.image = PhotoManagerGUI.enhanceImgList.pop()

        # Get the scale value.
        self.scaleVal = self.brightScale.get()
        
        # Enhances the image based on scale value.
        self.brightFactor = round(float(self.scaleVal) / 100, 1)

        # Store the brightness factor into the scaleValues dictionary.
        PhotoManagerGUI.scaleValues['brightness'] = self.brightFactor

        # Enhance Image:
        self.outImg = self.enhanceImg() 

        # Show the enhanced image.
        self.showImg(imgObj = self.outImg)
    
    #
    # This method enhances the Sharpness when the scale is changed.
    #             
    def enhanceImageSharpness(self, event):
        # Get the input image.
        self.image = PhotoManagerGUI.enhanceImgList.pop()

        # Get the scale value.
        self.scaleVal = self.sharpScale.get()
        
        # Enhances the image based on scale value.
        self.sharpFactor = round(float(self.scaleVal) / 100, 1)

        # Store the sharpness factor into the scaleValues dictionary.
        PhotoManagerGUI.scaleValues['sharpness'] = self.sharpFactor

        # Enhance Image:
        self.outImg = self.enhanceImg() 

        # Show the enhanced image.
        self.showImg(imgObj = self.outImg)
    #
    # This method finishes the enchance process.
    #
    def finishEnhance(self):
        self.image = PhotoManagerGUI.enhanceImgList.pop()
        self.showImg(imgObj = self.image, imgChg = True)
        PhotoManagerGUI.enhanceImgList = []
        self.sliderWindow.destroy()
    
    #
    # This method finishes the enchance process.
    #
    def clearEnhance(self):
        self.image = PhotoManagerGUI.enhanceImgList[0]
        self.showImg(imgObj = self.image)
        PhotoManagerGUI.enhanceImgList = []
        self.sliderWindow.destroy()
    #
    # This method resets the enchance process.
    #
    def resetEnhance(self):
        # set the initial values of the scales.
        self.setInitialValues()

        # set the initial values of the scale values dictionary.
        for self.key in PhotoManagerGUI.scaleValues.keys():
            PhotoManagerGUI.scaleValues[self.key] = 1.0

        # Enhance Image:
        self.outImg = self.enhanceImg()  

        # Show the enhanced image.
        self.showImg(imgObj = self.outImg)
    #
    # This method gets the initial x,y co-ordinate and starts drawing rectangular crop area.
    #
    def startCropArea(self, event):
        # Delete the crop area.
        self.disCanvas.delete(self.cropArea)

        # Get the start co-ordinates.
        self.startX, self.startY = event.x, event.y

        # Draw the initial rectangle crop area.
        self.cropArea = self.disCanvas.create_rectangle(self.startX, self.startY, self.startX + 1,
        self.startY + 1, fill = '', outline = 'black', width = 2)

    #
    # This method gets the x,y co-ordinates as the mouse moves and draws the rectangular crop area.
    #
    def drawCropArea(self, event):
        # Get the current co-ordinates.
        self.curX, self.curY = event.x, event.y

        # Draw the rectangular crop area.
        self.disCanvas.coords(self.cropArea, self.startX, self.startY, self.curX, self.curY)
    
    #
    # This method gets the final co-ordinates and enables the crop function. 
    #
    def enableCrop(self, event):
        # Get the final co-ordinates.
        self.finalX, self.finalY = event.x, event.y

        # Enable the crop function.
        self.edit.entryconfig('Crop', state = NORMAL)
    
    #
    # This method crops the curent image.
    #
    def corpImg(self):
        # Get the current image object from the stack.
        try:
            self.inputImg = PhotoManagerGUI.currImgObjStack[-1]
        except IndexError:
            messagebox.showwarning(title = 'Warning', message = 'Open a Picture!')
        else:
            # If the image is not thumbnail, then resize the image.
            if self.inputImg.size[0] <= 128 or self.inputImg.size[1] <= 128:
                self.tempImg = self.inputImg
            else:
                self.tempImg = self.inputImg.resize(PhotoManagerGUI.imgSize)
            
            # Crops the image using crop box.
            self.cropBox = (self.startX, self.startY, self.finalX, self.finalY)
            self.outImg = self.tempImg.crop(self.cropBox)

            # Delete the crop area.
            self.disCanvas.delete(self.cropArea)

            # Show the croped image.
            self.showImg(imgObj = self.outImg, imgChg = True)

# Main Function for the PhotoApp.

def main():
    root = Tk()
    PhotoApp = PhotoManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
