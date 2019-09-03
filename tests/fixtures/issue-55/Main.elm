module Main exposing (cool)

{-| blah
# blah
@docs cool
-}

import Color


{-| Convert a Color.Color into a Css.Color
toCssColor (Color.rgba 1.0 1.0 1.0 1.0) -- "{ alpha = 1, blue = 255, color = Compatible, green = 255, red = 255, value = "rgba(255, 255, 255, 1)" } : Css.Color"
-}
cool : Color.Color -> Color.Color
cool a =
    a
