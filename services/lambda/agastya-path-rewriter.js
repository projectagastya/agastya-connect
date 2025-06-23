/**
This functions is called agastya-path-rewriter and is in a file named index.js. It is in the us-east-1 region.
IAM role attached: agastya-path-rewriter-role
Permissions attached to IAM role: AWSLambdaBasicExecutionRole

Trust relationship: 

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com",
                    "edgelambda.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
**/

exports.handler = async (event) => {
    const request = event.Records[0].cf.request;
    const uri = request.uri;
    
    // Get the Host header - this will be the original domain at viewer-request stage
    const host = request.headers.host[0].value;
    
    console.log(`Processing viewer request for host: ${host}, URI: ${uri}`);
    
    // Route based on path
    if (uri === '/') {
        // Root path - serve different welcome pages based on domain
        if (host === 'agastyaconnect2.com') {
            request.uri = '/pages/welcome-2.html';
        } else {
            // Default for agastyaconnect.com and any other domain
            request.uri = '/pages/welcome.html';
        }
    } else if (uri === '/privacy') {
        request.uri = '/pages/privacy.html';
    } else if (uri === '/terms-of-service') {
        request.uri = '/pages/terms-of-service.html';
    } else if (uri.startsWith('/app/')) {
        // Let CloudFront behavior handle /app/* paths - route to ALB
        console.log(`App path detected: ${uri} - will route to ALB via CloudFront behavior`);
    } else if (!uri.startsWith('/pages/') && !uri.startsWith('/headshots/')) {
        // Serve 404 page for unknown paths based on domain
        console.log(`Unknown path: ${uri} - serving 404 page`);
        if (host === 'agastyaconnect2.com') {
            request.uri = '/pages/404-2.html';
        } else {
            request.uri = '/pages/404.html';
        }
    }
    
    console.log(`Final URI for host ${host}: ${request.uri}`);
    return request;
};