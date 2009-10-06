//
//  BinaryDataWriter.h
//
//  Copyright 2009 Dave Peck <davepeck [at] davepeck [dot] org>. All rights reserved.
//  http://davepeck.org/
//
//  This class makes it a little easier to write sequential binary files in Objective-C.
//
//  This code is released under the BSD license. If you use it in your product, please
//  let me know and, if possible, please put me in your credits.
//

#import <UIKit/UIKit.h>


@interface BinaryDataWriter : NSObject {
	BOOL littleEndian;
	NSStringEncoding encoding;
	NSMutableData *data;
}

+(id)emitterWithDefaultEncoding:(NSStringEncoding)defaultEncoding littleEndian:(BOOL)littleEndian;

-(void) writeEmptyBytes:(NSUInteger)count;
-(void) writeByte:(uint8_t)byte;
-(void) writeBytes:(const uint8_t *)bytes count:(NSUInteger)count;
-(void) writeData:(NSData *)data;
-(void) writeWord:(uint16_t)word;
-(void) writeDoubleWord:(uint32_t)doubleWord;
-(void) writeString:(NSString*)string;
-(void) writeString:(NSString*)string encoding:(NSStringEncoding)overrideEncoding;
-(void) writeNullTerminatedString:(NSString*)string;
-(void) writeNullTerminatedString:(NSString*)string encoding:(NSStringEncoding)overrideEncoding;
-(void) writeString:(NSString*)string withDelimiter:(uint8_t)delim;
-(void) writeString:(NSString*)string withDelimiter:(uint8_t)delim encoding:(NSStringEncoding)overrideEncoding;
-(void) writeArrayOfNullTerminatedStrings:(NSArray*)array;
-(void) writeArrayOfNullTerminatedStrings:(NSArray*)array encoding:(NSStringEncoding)overrideEncoding;

// After calling this routine, you will NOT be able to write any more.
-(NSData*) getData;

@end
