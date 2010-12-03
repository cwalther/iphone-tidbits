//
//  BinaryDataWriter.m
//
//  Copyright 2009 Dave Peck <davepeck [at] davepeck [dot] org>. All rights reserved.
//  http://davepeck.org/
//
//  This class makes it a little easier to write sequential binary files in Objective-C.
//
//  This code is released under the BSD license. If you use it in your product, please
//  let me know and, if possible, please put me in your credits.
//

#import "BinaryDataWriter.h"

// NS byte order stuff is not useful here -- CF byte order ensures we're always dealing
// with the right size on either 32 or 64 bit platforms.
#import <CoreFoundation/CFByteOrder.h>

@interface BinaryDataWriter (Private)
-(id)initWithDefaultEncoding:(NSStringEncoding)defaultEncoding littleEndian:(BOOL)isLittleEndian;
-(NSException *)buildEmitException;
-(void)dealloc;
@end

@implementation BinaryDataWriter (Private)
-(id)initWithDefaultEncoding:(NSStringEncoding)defaultEncoding littleEndian:(BOOL)isLittleEndian
{
    self = [super init];
    if (self != nil)
    {
        littleEndian = isLittleEndian;
        encoding = defaultEncoding;
        data = [[NSMutableData dataWithCapacity:256] retain];
    }
    return self;
}

-(NSException *)buildEmitException
{
    return [NSException exceptionWithName:@"BinaryDataWriterException" reason:@"Failure emitting desired information from the bytes." userInfo:nil];    
}

-(void)dealloc
{
    if (data != nil)
    {
        [data release];
        data = nil;
    }
    [super dealloc];
}
@end


@implementation BinaryDataWriter

+(id)emitterWithDefaultEncoding:(NSStringEncoding)defaultEncoding littleEndian:(BOOL)isLittleEndian
{
    return [[[BinaryDataWriter alloc] initWithDefaultEncoding:defaultEncoding littleEndian:isLittleEndian] autorelease];
}

-(void) writeEmptyBytes:(NSUInteger)count
{
    if (data == nil) { @throw [self buildEmitException]; }
    uint8_t *buffer = malloc(count);
    bzero(buffer, count);
    [data appendBytes:buffer length:count]; 
    free(buffer);
}

-(void) writeByte:(uint8_t)byte
{
    if (data == nil) { @throw [self buildEmitException]; }
    [data appendBytes:&byte length:1];
}

-(void) writeBytes:(const uint8_t *)bytes count:(NSUInteger)count
{
    if (data == nil) { @throw [self buildEmitException]; }
    [data appendBytes:bytes length:count];
}

-(void) writeData:(NSData *)appendage
{
    if (data == nil) { @throw [self buildEmitException]; }
    [data appendData:appendage];
}

-(void) writeWord:(uint16_t)word
{
    if (data == nil) { @throw [self buildEmitException]; }
    uint16_t safeWord; /* haha look what i called it */
    if (littleEndian)
    {
        safeWord = CFSwapInt16HostToLittle(word);
    }
    else
    {
        safeWord = CFSwapInt16HostToBig(word);
    }
    [data appendBytes:&safeWord length:2];
}

-(void) writeDoubleWord:(uint32_t)doubleWord
{
    if (data == nil) { @throw [self buildEmitException]; }
    uint32_t magicWord;
    if (littleEndian)
    {
        magicWord = CFSwapInt32HostToLittle(doubleWord);
    }
    else
    {
        magicWord = CFSwapInt32HostToBig(doubleWord);
    }
    [data appendBytes:&magicWord length:4];
}

-(void) writeString:(NSString*)string
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeString:string encoding:encoding];
}

-(void) writeString:(NSString*)string encoding:(NSStringEncoding)overrideEncoding
{
    if (data == nil) { @throw [self buildEmitException]; }
    [data appendData:[string dataUsingEncoding:overrideEncoding]];
}

-(void) writeNullTerminatedString:(NSString*)string
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeNullTerminatedString:string encoding:encoding];
}

-(void) writeNullTerminatedString:(NSString*)string encoding:(NSStringEncoding)overrideEncoding
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeString:string withDelimiter:0 encoding:overrideEncoding];
}

-(void) writeString:(NSString*)string withDelimiter:(uint8_t)delim
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeString:string withDelimiter:delim encoding:encoding];
}

-(void) writeString:(NSString*)string withDelimiter:(uint8_t)delim encoding:(NSStringEncoding)overrideEncoding
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeString:string encoding:overrideEncoding];
    [data appendBytes:&delim length:1];
}

-(void) writeArrayOfNullTerminatedStrings:(NSArray*)array
{
    if (data == nil) { @throw [self buildEmitException]; }
    [self writeArrayOfNullTerminatedStrings:array encoding:encoding];
}

-(void) writeArrayOfNullTerminatedStrings:(NSArray*)array encoding:(NSStringEncoding)overrideEncoding
{
    if (data == nil) { @throw [self buildEmitException]; }
    for (NSString *entry in array)
    {
        [self writeNullTerminatedString:entry encoding:overrideEncoding];
    }
}

-(NSData*) getData
{
    NSData *myData = [[data retain] autorelease];
    [data release];
    data = nil;
    return myData;
}

@end
