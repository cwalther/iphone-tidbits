Dave Peck's iPhone Tidbits
--------------------------

Here is a collection of code I've written for the iPhone that I've found useful in more than one project.

It is a fairly random collection. Currently we have:

1. **iOS Artwork Extractor** -- this python script is capable of extracting artwork packed in iOS SDK files ending with the `.artwork` extension. See the subdirectory README for details.

2. **FlickDynamics** -- implements the motion dynamics of Cocoa Touch's UIScrollView, but does so in a way that you can slot it in anywhere. I wrote it to handle scroll dynamics of a game's OpenGL|ES view. It is independent of coordinate system, etc.

3. **BinaryDataReader** and **BinaryDataWriter** -- read and write byte streams, deal with endian-ness, etc. Has been useful for cracking random/old binary file formats.

4. **JsonConnection** and **JsonResponse** -- makes it a little easier to talk to a JSON web service asynchronously. Deals with return content encodings, etc. Requires SBJSON.


All code is released under the BSD license.

If you use it in an app, please let me know! (And feel free to email me with any questions/submit any improvements.)

