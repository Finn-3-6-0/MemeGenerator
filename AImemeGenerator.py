from PIL import Image
from PIL import ImageDraw, ImageFont
import textwrap
from unsplash.api import Api
from unsplash.auth import Auth
import requests
from io import BytesIO
from google import genai
from google.genai import types
import os


def get_unsplash_img(client_id, client_secret, redirect_uri, code):

    auth = Auth(client_id, client_secret, redirect_uri, code=code)
    api = Api(auth)

    img_data = api.photo.random(query="funny")

    # If it's a ResultSet, extract first photo
    if isinstance(img_data, list) or hasattr(img_data, "__getitem__"):
        img_data = img_data[0]

    # Get the image URL
    img_url = img_data.urls.regular

    # Download the image
    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))

    # Resize for convienince of text placement
    if img.width != 1024 or img.height != 1024:
        img = img.resize((1024, 1024))
    else:
        print("Image is the right size!")

    return img


def get_ai_caption(client):
    # Give Gemmini Prompt to get a caption
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Generate one set of top and bottom text for a meme image "
        + ". Your top text should not exceed 36 characters, your bottom text should not exceed 36 characters you do not need to use all the characters available. "
        + "You MUST output 2 pieces of text in THIS FORMAT: (Top text,Bottom text). For example the output may look like: (Lorum ipsum,dolor sit amet). Do NOT give me anything other than the top and bottom text.",
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disables thinking
        ),
    )
    # Format the AI response
    top_and_bottom_text = response.text

    top_and_bottom_text = top_and_bottom_text.replace("(", "")
    top_and_bottom_text = top_and_bottom_text.replace(")", "")
    top_and_bottom_text = top_and_bottom_text.split(",")

    return top_and_bottom_text


def draw_text_on_image(caption_top, caption_bottom, img):
    # Call draw Method to add 2D graphics in an image
    image = ImageDraw.Draw(img)

    # VARS for img text and placement
    font_size = 120
    font = ImageFont.truetype("impact.ttf", font_size)

    width_div_two = img.width / 2
    height_div_two = img.height / 2

    height_for_bot = img.height * 0.825
    height_for_top = img.height * 0.001

    # if bottom cap exceeds 20 chars thenit has to move up
    char_counter = 0
    for char in caption_bottom:
        char_counter = char_counter + 1

    if char_counter > 20:
        height_for_bot = img.height * 0.725

    # Top Text
    image.text(
        (width_div_two, height_for_top),
        textwrap.fill(caption_top, width=18),
        fill=(255, 255, 255),
        font=font,
        align="center",
        anchor="ma",
        stroke_width=4,
        stroke_fill="black",
    )
    # Bottom Text
    image.text(
        (width_div_two, height_for_bot),
        textwrap.fill(caption_bottom, width=20),
        fill=(255, 255, 255),
        font=font,
        align="center",
        anchor="ma",
        stroke_width=4,
        stroke_fill="black",
    )

    # Save the edited image
    img.save("meme.jpeg")


def main():
    # Gemini API key
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    # Unsplash API keys
    client_id = os.environ.get("UNSPLASH_CLIENT_ID")
    client_secret = os.environ.get("UNSPLASH_CLIENT_SECRET")
    redirect_uri = os.environ.get("UNSPLASH_REDIRECT_URI")
    code = ""

    # Get Image
    img = get_unsplash_img(client_id, client_secret, redirect_uri, code)

    # Get and format the text for image
    top_and_bottom_text = get_ai_caption(client)
    caption_top = top_and_bottom_text[0]
    caption_bottom = top_and_bottom_text[1]

    # Put the text on the image with textwrapping
    draw_text_on_image(caption_top, caption_bottom, img)

    # Display edited image
    img.show()


if __name__ == "__main__":
    main()
