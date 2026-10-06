from modules.image_generator import generate_image


prompt = """
A cinematic magical library hidden beneath a school,
filled with ancient glowing books, mysterious blue light,
wooden bookshelves, a young girl standing at the entrance,
fantasy adventure atmosphere, detailed digital art,
wide cinematic storyboard composition.
"""


output_path = "generated/images/test_image.png"


try:

    result = generate_image(
        prompt,
        output_path
    )

    print("IMAGE GENERATED SUCCESSFULLY!")
    print("Saved to:", result)

except Exception as e:

    print("IMAGE GENERATION FAILED!")
    print(type(e).__name__)
    print(str(e))