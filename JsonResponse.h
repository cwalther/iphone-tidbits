//
//  JsonResponse.h
//
//  The successful value returned by a JsonConnection.
//

#import <Foundation/Foundation.h>


@interface JsonResponse : NSObject {
    NSArray *array;
    NSDictionary *dictionary;
}

+ (id)jsonResponseWithString:(id)jsonString; /* nil indicates failure */
- (id)initWithString:(id)jsonString;

- (BOOL)isArray;
- (BOOL)isDictionary;

- (NSArray *)array;
- (NSDictionary *)dictionary;

@end
