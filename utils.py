# utils.py
def wrap_text(text, box_width, font_scale=0.5, thickness=1):
    import cv2
    wrapped_lines = []
    words = text.split(' ')
    current_line = words[0]

    for word in words[1:]:
        if cv2.getTextSize(current_line + ' ' + word, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0][0] < box_width:
            current_line += ' ' + word
        else:
            wrapped_lines.append(current_line)
            current_line = word
    wrapped_lines.append(current_line)

    return wrapped_lines

def draw_face_boxes_with_descriptions(frame, face_locations, labels, face_descriptions):
    import cv2
    from .utils import wrap_text
    for (top, right, bottom, left), label, description in zip(face_locations, labels, face_descriptions):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 10 if top - 10 > 10 else top + 10
        cv2.putText(frame, label, (left, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        wrapped_text = wrap_text(description, right - left)
        for i, line in enumerate(wrapped_text):
            cv2.putText(frame, line, (left, y + (i * 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame
