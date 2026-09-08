import streamlit as st

from src.config import FORESIGHT_BASE_WEEK


def show_page():
    st.title("📖 Info Page")
    st.header("Welcome to the Great Fantasy Bake Off League!")
    st.markdown(
        """
    On your marks, get set, predict! This season, we’re adding a new layer of fun to our weekly viewing with a fantasy league. 
    The goal is simple: prove you have the best eye for baking talent by accurately predicting both the weekly events and the season's ultimate champions.
    """
    )
    st.markdown("---")

    st.subheader("How to Play: Your Weekly Signature Bake")
    st.markdown(
        """
    Each week of the competition (starting with Episode 2), you will submit a fresh set of predictions before the episode airs.
    Your weekly submission must now include **six** predictions:
    - **Star Baker**: Who will be the week's top baker?
    - **Technical Challenge Winner**: Who will come in first in the technical?
    - **Baker Sent Home**: Who will be eliminated from the competition?
    - **Hollywood Handshake**: Will anyone get a handshake? (Optional, high-reward pick).
    - **Predicted Season Winner**: Who do you think will win the entire competition?
    - **Predicted Finalists (x2)**: Who will the other two finalists be?

    Your predictions for the season winner and finalists can change week to week as you see how the bakers perform.
    """
    )
    st.markdown("---")

    st.subheader("Scoring: The Recipe for Victory")
    st.markdown(
        "Your grand total will be a combination of two types of points: **Weekly Points** and **Foresight Points**."
    )

    st.write("#### 1. Weekly Points")
    st.markdown(
        """These are straightforward points for correctly predicting the episode's key events.
    __Note: Points are may be awarded or penalized, as shown below.__
    __There is no penalty for saying there will be no handshake and one is given.__
    """
    )
    st.markdown(
        """
    | Correct Prediction                 | Points Awarded |
    |------------------------------------|----------------|
    | Handshake Predicted and Given      | 10 points      |
    | Star Baker                         | 5 points       |
    | Baker Sent Home                    | 5 points       |
    | Technical Challenge Winner         | 3 points       |

    | Penalties                          | Points Removed |
    |------------------------------------|----------------|
    | Handshake Predicted, None Given    | 10 points      |
    | Predicted Star Baker is sent home  | 5 points       |
    | Predicted Baker Sent Home is Star  | 5 points       |
    """
    )

    st.write("#### 2. Foresight Points: The Weighted Bonus")
    st.markdown(
        f"""
    This is where strategy comes in. You earn points for correctly predicting the season's
    champion and finalists, and calls made **earlier in the season are worth far more**.

    Your season predictions are logged every week, but foresight points stay hidden until the
    winner is crowned — then they all resolve at once.

    - **Champion**: correctly naming the eventual winner in your **Season Winner** slot is worth
      `({FORESIGHT_BASE_WEEK} − week) × 10`.
    - **Finalists**: each of the three actual finalists you named anywhere in your predictions
      (the champion counts as a finalist too!) is worth `({FORESIGHT_BASE_WEEK} − week) × 5`.
    - **Only your earliest correct week counts** for each pick. Re-submitting the same correct
      prediction later doesn't stack — this rewards *conviction*, not repetition. So lock in a
      call you believe in early and let it ride.
    - **Example**: naming the winner in Week 2 is worth **{(FORESIGHT_BASE_WEEK - 2) * 10} points**
      `(({FORESIGHT_BASE_WEEK}−2) × 10)`. Waiting until Week 9 to first make that same correct call
      is worth only **{(FORESIGHT_BASE_WEEK - 9) * 10} points** `(({FORESIGHT_BASE_WEEK}−9) × 10)`.
    """
    )
