{-| @docs should list all exposed functions -}
module PublicFunctionNotInAtDocs exposing (anotherPublicFunc, publicFunc)

{-|

@docs anotherPublicFunc
-}


{-|
-}
publicFunc x =
    x + 1


{-|
-}
anotherPublicFunc x =
    x - 1
