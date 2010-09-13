iPhone Artwork Extractor
========================

You may have noticed that most of Apple's iPhone artwork is packaged in files ending with the `.artwork` extension. The iPhone Artwork Tool makes it easy to export images from those files. Exporting is useful for certain iPhone development tasks. The tool also supports creating *new* `.artwork` files from images that you've tweaked; this is useful if you want to create mods that change the basic appearance of the iPhone's interface.

The software is written in python. You must have python 2.x and the [Python Imaging Library](http://www.pythonware.com/products/pil/) installed in order for it to work. If you're using OSX, I suggest using [MacPorts](http://www.macports.org/) to install the PIL. On Windows, it is easiest to just install Python and the PIL directly from the installer executables.

Because each artwork file is different, I only support four at the moment:

    .../iPhoneSimulator4.1.sdk/System/Library/Frameworks/UIKit.framework/Shared~iphone.artwork
    .../iPhoneSimulator4.1.sdk/System/Library/Frameworks/UIKit.framework/Shared~ipad.artwork
    .../iPhoneSimulator4.1.sdk/System/Library/Frameworks/UIKit.framework/Shared@2x~iphone.artwork
    .../iPhoneSimulator4.1.sdk/System/Library/Frameworks/UIKit.framework/Shared@2x~ipad.artwork
        
To get going, download the python source code.

Next, find the appropriate artwork files on disk. This tool supports iPhone OS 2.0.0, 2.2.0, 3.2.0, and 4.1.0 artwork files.

### EXPORTING

To get the images out of a `.artwork` file, you *export* them. This fills a directory of your choosing with easily editable PNG files.

To export, run the tool as follows:

    python ./iphone-artwork.py -export Keyboard-Latin.artwork ./img

That's all there is to it!

### IMPORTING

It is equally easy to turn a directory full of PNGs into a new `.artwork` file.

To import, run the tool as follows:

    python ./iphone-artwork.py -import Keyboard-Latin.artwork ./img Final.artwork

This will read all the PNGs in the `img` directory and place them in the file named `Final.artwork`. Again, easy!

You may wonder why you have to supply the *original* `Keyboard-Latin.artwork` file in this example. The reason is that in iPhone OS, the artwork files sometimes contain extra data that is *not* image data. And of course it is important to keep this data around. So we only use the original `.artwork` file for *reading* in this example -- of course, we never write to it!

### VERSION HISTORY

    v0.8  9/13/2010 - (CURRENT) support iPhone OS 4.1.0 and 3.2.0 artwork files.
    v0.7 12/07/2008 - support iPhone OS 2.2.0 artwork files from UIKit
    v0.6  7/28/2008 - support other image formats besides RGBA. Fix a filename-related bug (used relative name instead of absolute.)
    v0.5  7/25/2008 - add support for MobilePhone images, and clean up usage messages.
    v0.4  7/24/2008 - add feature support for -import so that you can make artwork files
    v0.3  7/19/2008 - use os.path to manipulate paths so that things work nicely on windows
    v0.2  7/18/2008 - change command line structure to use -export (preparing to also add -import) and fix bugs in usage_* methods
    v0.1  7/13/2008 - released initial version, with export support for all 2.0.0 UIKit artwork
    
### Contact Me

Feel free to send comments, suggestions, and improvements my way. See code comments for details on making improvements. You can find my email address in the information area below.
