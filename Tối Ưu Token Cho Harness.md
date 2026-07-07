# **Nghiên cứu Kỹ thuật Nén Token và Thiết kế Kiến trúc Tối ưu hóa Chi phí cho Hệ thống Kiểm thử LLM**

Sự bùng nổ của các ứng dụng dựa trên mô hình ngôn ngữ lớn (LLM) kéo theo nhu cầu cấp thiết về việc xây dựng các hệ thống kiểm thử và đánh giá tự động (Evaluation Harness)1. Tuy nhiên, chi phí vận hành các hệ thống này đang trở thành một rào cản tài chính lớn do lượng ngữ cảnh đầu vào (input tokens) và phản hồi đầu ra (output tokens) quá đồ sộ2. Báo cáo kỹ thuật này cung cấp một nghiên cứu chuyên sâu về các giải pháp nén token ở tầng dữ liệu, tối ưu hóa kiến trúc điều phối hệ thống và phân tích tokenizer nhằm xây dựng một hệ thống harness hiệu năng cao với chi phí tối thiểu.

## **Tổng quan và So sánh Định lượng các Kỹ thuật Nén Token**

Để thiết lập một cái nhìn toàn diện trước khi đi vào chi tiết kỹ thuật, bảng dưới đây tổng hợp các thông số hiệu năng, mức độ bảo toàn độ chính xác, độ trễ hệ thống và độ phức tạp mã nguồn của các kỹ thuật nén token chính khi tích hợp vào một hệ thống harness tự xây dựng:

| Nhóm Giải pháp | Kỹ thuật Đặc thù | % Token Tiết kiệm | Ảnh hưởng đến Độ chính xác (Accuracy) | Độ trễ Tăng thêm (Latency Overhead) | Độ phức tạp Triển khai |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Tầng Dữ liệu / Prompt** | Loại bỏ từ dừng (Stopwords) & Lọc Heuristic4 | ![][image1] | Giảm nhẹ (![][image2]) do mất tính tự nhiên của câu5. | Rất thấp (![][image3] trên CPU) | Thấp5 |
|  | Cắt tỉa cú pháp (Syntactic Pruning \- spaCy)7 | ![][image4] | Duy trì ổn định (![][image5] biến động)8. | Thấp (![][image6] trên CPU)7 | Trung bình8 |
|  | Nén dựa trên SLM (LLMLingua-2)9 | ![][image7] (Tỷ lệ nén ![][image8])9 | Bảo toàn sai số ở mức tối thiểu (![][image5] biến động)9. | Thấp (![][image9] trên GPU)9 | Cao (Yêu cầu host mô hình SLM)10 |
|  | Nén định hướng câu hỏi (LongLLMLingua)13 | ![][image10] (Tỷ lệ nén ![][image11])9 | Tăng độ chính xác RAG (![][image12]) nhờ giảm nhiễu13. | Trung bình (![][image13] trên GPU)14 | Cao (Yêu cầu pipeline truy xuất tích hợp)9 |
| **Kiến trúc Harness** | Bộ nhớ đệm Prompt (Prompt Caching)17 | ![][image14] (Phụ thuộc vào tần suất trúng cache)17 | Giữ nguyên tuyệt đối (![][image15] ảnh hưởng)19. | Giảm thời gian phản hồi đầu tiên tới ![][image7]17. | Thấp đến Trung bình17 |
|  | Gom cụm Prompt (Batch Prompting)22 | Giảm tới ![][image16] tổng lượng token đầu vào22. | Biến động trong khoảng ![][image17] với kích thước lô (batch size) dưới 10022. | Tăng thời gian phản hồi đơn lẻ, giảm mạnh tổng thời gian xử lý lô. | Trung bình24 |
|  | Quản lý lịch sử bằng Bộ nhớ lai (CALMem)25 | ![][image7] | Duy trì ngữ cảnh tốt hơn so với cơ chế cửa sổ trượt đơn thuần26. | Thấp (![][image18] truy vấn vector)27. | Cao26 |
| **Tầng Tokenizer** | Định dạng dữ liệu tối ưu (LEAN / TOON)28 | ![][image19] so với JSON định dạng chuẩn28. | Cải thiện độ chính xác (![][image20]) nhờ giảm nhiễu cú pháp28. | Không phát sinh trễ (Xử lý chuỗi thuần túy)31. | Trung bình29 |

## **Phân tích và Hướng dẫn Triển khai Kỹ thuật Nén ở Tầng Dữ liệu**

### **Các Phương pháp Rút gọn Văn bản Tự nhiên (Heuristic-based)**

Các phương pháp heuristic truyền thống hướng tới việc cắt bỏ các thành phần ngôn ngữ thừa thãi đối với máy tính nhưng cần thiết cho con người4. Phương pháp loại bỏ từ dừng (Stopwords removal) lọc đi các từ nối có tần suất xuất hiện cao nhưng mang lượng thông tin (entropy) thấp4. Tuy nhiên, việc áp dụng thô bạo có thể phá vỡ cấu trúc ngữ pháp và làm giảm khả năng hiểu ngữ cảnh của LLM5.  
Kỹ thuật cắt tỉa cú pháp (Syntactic Pruning) dựa trên phân tích cây cú pháp của thư viện spaCy cung cấp giải pháp an toàn hơn7. Bằng cách phân tích mối quan hệ phụ thuộc (dependency parsing), hệ thống xác định các cụm danh từ (noun chunks) làm mốc thông tin cốt lõi, từ đó loại bỏ các trạng từ bổ trợ, mệnh đề phụ hoặc các định từ không quan trọng mà không làm đứt gãy mạch logic chính của câu7.  
Dưới đây là mã nguồn Python tích hợp bộ lọc cắt tỉa cú pháp bằng spaCy vào hệ thống harness:

Python  
import spacy

def syntactic\_prune(text: str, preserve\_pos=None, preserve\_deps=None) \-\> str:  
    """  
    Thực hiện cắt tỉa cú pháp dựa trên phân tích cây phụ thuộc của spaCy.  
    Loại bỏ các từ không mang thông tin cốt lõi nhưng vẫn giữ cấu trúc câu logic.  
    """  
    try:  
        nlp \= spacy.load("en\_core\_web\_sm")  
    except OSError:  
        from spacy.cli import download  
        download("en\_core\_web\_sm")  
        nlp \= spacy.load("en\_core\_web\_sm")  
          
    doc \= nlp(text)  
      
    if preserve\_pos is None:  
        preserve\_pos \= {"NOUN", "VERB", "PROPN", "NUM", "PRON"}  
    if preserve\_deps is None:  
        preserve\_deps \= {"nsubj", "dobj", "ROOT", "pobj", "ccomp"}  
          
    pruned\_tokens \= \[\]  
    for token in doc:  
        \# Giữ lại các token nếu chúng thuộc nhóm từ loại quan trọng hoặc giữ vai trò chủ chốt trong cây cú pháp  
        if (token.pos\_ in preserve\_pos or   
            token.dep\_ in preserve\_deps or   
            token.is\_ent or   
            token.text.lower() in {"not", "no", "never"}): \# Giữ lại các trạng từ phủ định tránh đảo ngược nghĩa  
            pruned\_tokens.append(token.text\_with\_ws)  
              
    return "".join(pruned\_tokens).strip()

### **Kỹ thuật Sử dụng Mô hình Nhỏ để Nén Dữ liệu cho Mô hình Lớn**

Xu hướng hiện đại chuyển dịch từ việc nén dựa trên luật sang sử dụng các mô hình ngôn ngữ nhỏ (SLM) làm bộ nén phân phối thông tin13.

* **Selective-Context**: Sử dụng một mô hình ngôn ngữ nhân quả (Causal LM) nhỏ (như GPT-2) để tính toán độ tự thông tin (self-information) của các đơn vị từ vựng5. Các phân đoạn văn bản có lượng thông tin thấp hơn một ngưỡng quy định sẽ bị cắt bỏ8. Tuy nhiên, phương pháp này gặp hạn chế lớn do các mô hình nhân quả chỉ tính toán ngữ cảnh một chiều (unidirectional context), bỏ qua mối liên kết ngữ nghĩa hai chiều9.  
* **LLMLingua**: Giải quyết bài toán nén bằng cách sử dụng bộ điều khiển ngân sách (budget controller) và thuật toán nén lặp cấp độ token để duy trì tính toàn vẹn ngữ nghĩa ở các tỷ lệ nén cực đoan lên tới ![][image21]33. Dẫu vậy, phương pháp này vẫn chịu ảnh hưởng từ chi phí tính toán perplexity lớn của các mô hình giải mã tự hồi quy9.  
* **LLMLingua-2**: Chuyển đổi bài toán nén prompt thành bài toán phân loại token (token classification) nhị phân9. Hệ thống sử dụng kỹ thuật chưng cất dữ liệu (data distillation) từ mô hình GPT-4 để dán nhãn dữ liệu huấn luyện (giữ lại hay loại bỏ)9. Mô hình nén cốt lõi dựa trên kiến trúc mã hóa Transformer hai chiều (như XLM-RoBERTa-large với 355 triệu tham số hoặc mBERT với 110 triệu tham số)10.

![][image22]  
Kỹ thuật này đạt hiệu quả vượt trội: tốc độ nén nhanh hơn gấp ![][image23] so với phiên bản LLMLingua thế hệ đầu, giảm tải tài nguyên GPU xuống mức tối thiểu (chỉ cần khoảng ![][image24] VRAM trên kiến trúc V100) và duy trì sự ổn định của hiệu năng hạ nguồn trên đa dạng tác vụ mà không gây ra hiện tượng ảo giác (hallucination) do tính chất trích xuất nguyên bản (extractive pruning)9.

* **LongLLMLingua**: Được tối ưu hóa chuyên biệt cho các kịch bản ngữ cảnh dài hoặc hệ thống truy xuất RAG14. Nó sử dụng cơ chế tính toán độ tương đồng định hướng câu hỏi (question-aware perplexity) để đánh giá tầm quan trọng của từng đoạn văn bản đối với câu hỏi đầu vào14. Bằng cách sắp xếp lại và đưa các thông tin quan trọng nhất ra hai biên của prompt, LongLLMLingua giải quyết triệt để hiện tượng mất thông tin ở giữa (lost-in-the-middle) của các LLM thương mại, giúp cải thiện độ chính xác của mô hình đầu ra lên tới ![][image25] trong khi giảm ![][image26] lượng token cần xử lý13.

Dưới đây là hướng dẫn tích hợp LLMLingua-2 trực tiếp vào hệ thống harness bằng Python:

Python  
from llmlingua import PromptCompressor

def compress\_prompt\_with\_lingua(prompt: str, rate: float \= 0.5) \-\> dict:  
    """  
    Sử dụng LLMLingua-2 với mô hình XLM-RoBERTa-large để nén prompt đầu vào.  
    Mô hình này hoạt động hiệu quả trên GPU và tối ưu hóa thời gian xử lý.  
    """  
    \# Khởi tạo compressor sử dụng mô hình LLMLingua-2-large  
    compressor \= PromptCompressor(  
        model\_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",  
        use\_llmlingua2=True  
    )  
      
    \# Thực hiện nén prompt với tỷ lệ giữ lại (rate) mong muốn  
    compressed\_results \= compressor.compress\_prompt(  
        prompt,  
        rate=rate,  
        force\_tokens=\["\[INST\]", "\[/INST\]", "SYS\_META"\], \# Bảo toàn các token cấu trúc quan trọng  
        drop\_consecutive=False  
    )  
      
    return {  
        "compressed\_prompt": compressed\_results\["compressed\_prompt"\],  
        "original\_tokens": compressed\_results\["origin\_tokens"\],  
        "compressed\_tokens": compressed\_results\["compressed\_tokens"\],  
        "savings\_ratio": compressed\_results\["ratio"\]  
    }

### **Tối ưu hóa Prompt Template**

Để giảm lượng token cố định (static tokens) phát sinh trong mỗi lượt chạy kiểm thử, cấu trúc mẫu prompt cần được tinh giản triệt để thông qua kỹ thuật chưng cất chỉ dẫn (instruction distillation)2. Thay vì mô tả các ràng buộc hành vi bằng các đoạn văn tự nhiên dài dòng, cấu trúc prompt cần được chuyển dịch sang dạng khai báo thuộc tính cô đọng2.  
Các ví dụ few-shot nên được thiết kế dưới dạng đại diện tối thiểu hóa2. Việc thay thế hệ thống hướng dẫn dài bằng các ký pháp ngắn gọn cho phép mô hình dễ dàng tiếp thu mà không tốn context window dư thừa2. Ví dụ, một hệ thống hướng dẫn dài dòng như: *"Bạn là một trợ lý đánh giá mã nguồn chuyên nghiệp. Hãy phân tích kỹ đoạn code dưới đây, tìm ra các lỗi bảo mật nguy hiểm và trả về kết quả dưới dạng cấu trúc JSON chính xác tuyệt đối, không được thêm bất kỳ câu hội thoại nào xung quanh."* (![][image27] tokens) có thể được chuyển đổi thành một khai báo ngắn gọn: *"Act: CodeEvaluator. Task: Vulnerability Audit. Output: JSON only. No chat."* (![][image28] tokens)2.

## **Tối ưu hóa ở Tầng Kiến trúc Hệ thống Harness**

### **Thiết kế Cơ chế Bộ nhớ đệm Prompt (Prompt Caching)**

Prompt Caching là đòn bẩy kỹ thuật mang lại tỷ suất hoàn vốn (ROI) cao nhất cho các hệ thống harness tự xây dựng chạy các bài đánh giá lặp đi lặp lại trên cùng một bộ khung chỉ dẫn hoặc cơ sở tri thức19. Cơ chế này hoạt động dựa trên việc lưu trữ các trạng thái khóa-giá trị (KV Cache) của các phân đoạn tiền tố trùng lặp hoàn hảo trong chuỗi đầu vào17.  
Các nhà cung cấp dịch vụ đám mây áp dụng các chính sách kỹ thuật và tài chính khác nhau cho tính năng này, được tổng hợp chi tiết trong bảng dưới đây:

| Nhà cung cấp | Ngưỡng kích hoạt tối thiểu (Min Tokens) | Chi phí ghi bộ đệm (Cache Write) | Chi phí đọc bộ đệm (Cache Hit) | Thời gian sống mặc định (TTL) | Tham số điều hướng tối ưu |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **OpenAI** | **![][image29]** tokens34 | Miễn phí (Bằng giá input tiêu chuẩn)21 | Giảm giá từ ![][image7] tùy dòng model17. | ![][image30] phút (Tự động gia hạn khi có hit)21. | prompt\_cache\_key \[cite: 17\] |
| **Anthropic** | **![][image29]** (Sonnet 3.x/4.1) / ![][image31] (Sonnet 4.6) / ![][image32] (Opus 4.6)34 | Tính thêm phí phạt: ![][image33] (TTL ![][image34]) hoặc ![][image35] (TTL ![][image36])36. | Giảm giá ![][image37] so với input tiêu chuẩn21. | ![][image38] phút (mặc định) đến ![][image39] giờ (tùy chọn)36. | Khai báo tường minh cache\_control36. |
| **DeepSeek** | **![][image40]** (Tự động kích hoạt từ token đầu tiên)37 | Miễn phí (Bằng giá input tiêu chuẩn)36 | Giảm giá cực sâu (![][image41]), chỉ ![][image42] tokens21. | Tự động dọn dẹp theo chính sách LRU (Least Recently Used)37. | So khớp tiền tố tự động từ token thứ ![][image40]37. |

Để tối đa hóa tỷ lệ trúng cache (Cache Hit Rate), kiến trúc harness bắt buộc phải phân tách prompt thành cấu trúc hai tầng rõ rệt: phần tĩnh (Static Prefix) bao gồm System Prompt, mô tả công cụ (Tool Schemas), toàn bộ các ví dụ few-shot đặt ở phần đầu của chuỗi đầu vào17; và phần động (Dynamic Suffix) bao gồm mã nguồn hoặc câu hỏi truy vấn động được đặt ở cuối cùng38. Bất kỳ sự thay đổi ký tự nào ở phần đầu sẽ ngay lập tức làm vô hiệu hóa toàn bộ vùng đệm phía sau39.  
Dưới đây là hướng dẫn triển khai tích hợp cơ chế bộ nhớ đệm kép tương thích cho cả OpenAI và Anthropic Claude trong hệ thống harness:

Python  
import openai  
import anthropic

def execute\_evaluation\_with\_cache(  
    system\_prompt: str,   
    few\_shot\_examples: str,   
    dynamic\_payload: str,   
    provider: str \= "openai"  
) \-\> str:  
    """  
    Thực thi cuộc gọi API tối ưu hóa bộ nhớ đệm dựa trên nhà cung cấp dịch vụ.  
    """  
    if provider \== "anthropic":  
        client \= anthropic.Anthropic()  
        \# Đối với Anthropic, ta chỉ định ranh giới bộ đệm một cách tường minh  
        response \= client.messages.create(  
            model="claude-3-7-sonnet-20250219-v1:0",  
            max\_tokens=1000,  
            system=\[  
                {  
                    "type": "text",  
                    "text": system\_prompt,  
                    "cache\_control": {"type": "ephemeral"} \# Đánh dấu lưu cache phần System Prompt  
                },  
                {  
                    "type": "text",  
                    "text": few\_shot\_examples,  
                    "cache\_control": {"type": "ephemeral"} \# Đánh dấu lưu cache phần Few-shot  
                }  
            \],  
            messages=\[  
                {  
                    "role": "user",  
                    "content": dynamic\_payload \# Phần động không gắn cache\_control  
                }  
            \]  
        )  
        return response.content\[0\].text

    elif provider \== "openai":  
        client \= openai.OpenAI()  
        \# OpenAI tự động nhận diện cache cho các tiền tố trên 1024 tokens.  
        \# Ta có thể truyền thêm thuộc tính prompt\_cache\_key để cải thiện hiệu năng định tuyến.  
        full\_prompt \= f"{system\_prompt}\\n\\n{few\_shot\_examples}\\n\\nUser: {dynamic\_payload}"  
        response \= client.chat.completions.create(  
            model="gpt-4o",  
            messages=\[{"role": "user", "content": full\_prompt}\],  
            extra\_body={"prompt\_cache\_key": "harness\_eval\_static\_prefix"} \# Gợi ý định tuyến đến server chứa cache  
        )  
        return response.choices\[0\].message.content

### **Kỹ thuật Phân tách Prompt (Prompt Chaining) so với Gom cụm Prompt (Batching)**

Việc lựa chọn giữa việc gom cụm các yêu cầu đánh giá hay chia nhỏ chúng thành một chuỗi các bước suy luận tuần tự phụ thuộc vào cấu trúc bài toán và các mô hình đích sử dụng:

* **Gom cụm Prompt (Batch Prompting / Variable Stacking)**: Thích hợp cho các tác vụ phân loại lớn hoặc trích xuất dữ liệu hàng loạt22. Bằng cách nhồi nhiều mẫu đánh giá (ví dụ: ![][image43] đoạn code ngắn hoặc các dòng nhật ký hệ thống) vào trong một lần gọi API duy nhất, hệ thống chỉ phải trả phí cho phần System Prompt tĩnh đúng một lần thay vì phải nhân lên ![][image44] lần22. Kỹ thuật này giúp tiết kiệm trung bình hơn ![][image16] chi phí token đầu vào22.  
  Đặc biệt đối với các mô hình lý luận lớn (Large Reasoning Models \- LRMs) như DeepSeek-R1 hay OpenAI o1, batch prompting hoạt động như một bộ điều hòa thời gian suy luận (inference-time regularizer)23. Việc xử lý song song nhiều mẫu buộc mô hình phải giới hạn độ sâu suy nghĩ thừa thãi (overthinking), giảm thiểu các cụm từ rườm rà, tự sửa lỗi lặp đi lặp lại, giúp giảm số lượng token suy nghĩ (reasoning tokens) tạo ra lên tới ![][image45] trong khi chất lượng đánh giá vẫn được duy trì ổn định23.  
* **Phân tách Prompt (Prompt Chaining)**: Nên áp dụng khi quy trình đánh giá yêu cầu logic phân nhánh phức tạp, hoặc khi kết quả của bước sau phụ thuộc trực tiếp vào kết quả của bước trước41. Mặc dù chaining làm tăng tổng lượng token đầu vào do phải lặp lại hệ thống chỉ dẫn ở mỗi chặng, nó mang lại tính minh bạch cao, dễ kiểm thử lỗi ở từng khâu và ngăn chặn hiện tượng trôi lệch ngữ nghĩa của mô hình24.

### **Quản lý Trạng thái và Lịch sử Hội thoại trong Harness**

Trong các bài kiểm thử dạng agent hoặc hội thoại đa bước dài, việc gửi lại toàn bộ lịch sử trò chuyện qua mỗi lượt suy luận sẽ nhanh chóng làm tràn context window và tiêu tốn ngân sách một cách phi mã3. Ba chiến lược quản lý trạng thái sau đây được cân nhắc lựa chọn tùy theo yêu cầu đặc thù:

| Chiến lược Quản lý Bộ nhớ | Ưu điểm chính | Nhược điểm lớn | Chi phí Token phát sinh | Phù hợp nhất cho |
| :---- | :---- | :---- | :---- | :---- |
| **Cửa sổ trượt (Sliding Window)** \[cite: 26, 42\] | Dự đoán được chi phí token cố định, dễ hiện thực3. | Mất hoàn toàn ngữ cảnh cũ ở các lượt tương tác đầu26. | Cực kỳ thấp3. | Trò chuyện ngắn dưới 15-20 lượt tương tác27. |
| **Tóm tắt hội thoại lũy tiến (Recursive Summary)** \[cite: 2, 42\] | Bảo toàn nội dung chính, tích hợp mượt mà với Prompt Caching26. | Mất chi tiết kỹ thuật nhỏ (mã định danh, đoạn code ngắn)26. | Phát sinh chi phí gọi mô hình phụ để tóm tắt liên tục27. | Đánh giá hội thoại tổng quát, phân tích trạng thái logic26. |
| **Trí nhớ lai dựa trên Vector (CALMem)** \[cite: 25\] | Truy cập được thông tin hội thoại cực dài từ các phiên trước27. | Đòi hỏi hạ tầng Vector DB; phụ thuộc vào độ chính xác của Embedding27. | Phát sinh token cho truy vấn vector và lưu trữ metadata27. | Agent thực hiện kiểm thử dài hơi, đa phiên làm việc27. |

## **Phân tích Tokenizer và Tối ưu hóa Định dạng Dữ liệu**

### **Sự khác biệt về Tokenizer giữa các dòng mô hình**

Hiệu năng mã hóa của các bộ tokenizer đóng vai trò quyết định đến chi phí thực tế phát sinh trên mỗi yêu cầu gọi API44. Các thế hệ tokenizer mới (như bộ mã hóa o200k\_base của OpenAI dùng cho GPT-5 và GPT-4o) có kích thước từ điển từ vựng lớn hơn vượt trội so với các bộ tokenizer cũ của Llama hay Claude28. Điều này giúp chúng biểu diễn cùng một khối lượng thông tin văn bản với số lượng token ít hơn đáng kể, đặc biệt là đối với các ký tự đặc biệt, mã nguồn hoặc dữ liệu có cấu trúc phức tạp28.

### **Tối ưu hóa Định dạng Dữ liệu Truyền tải**

Khi đưa dữ liệu có cấu trúc vào trong ngữ cảnh của mô hình (ví dụ: kết quả chạy thử nghiệm code, thông số tài nguyên hệ thống, dữ liệu bảng), việc lựa chọn định dạng tuần tự hóa (serialization format) ảnh hưởng cực kỳ lớn đến cả lượng token tiêu hao lẫn độ chính xác của kết quả suy luận44.

* **JSON**: Mặc dù là tiêu chuẩn phổ biến nhất trong phát triển phần mềm, JSON cực kỳ kém hiệu quả về mặt token khi đưa vào LLM do tính chất rườm rà44. Việc lặp đi lặp lại các khóa (keys), các dấu ngoặc nhọn, dấu ngoặc vuông và dấu nháy kép tiêu tốn tới ![][image46] tổng lượng token của một danh sách đối tượng44.  
* **XML**: Đây là định dạng tồi nhất về hiệu năng token44. Các thẻ đóng lặp lại liên tục khiến XML tiêu tốn thêm khoảng ![][image47] tokens so với JSON định dạng chuẩn và hơn ![][image16] so với các định dạng tối giản như Markdown, đồng thời làm giảm hiệu năng xử lý của các mô hình cỡ nhỏ do độ nhiễu ký tự quá cao44.  
* **YAML / Markdown**: Là các phương án thay thế có tính thực tiễn cao mà không yêu cầu viết thêm bộ phân tách phức tạp28. Markdown tiết kiệm từ ![][image48] lượng token tiêu hao so với JSON trong khi YAML tiết kiệm khoảng ![][image49], đồng thời giữ nguyên hoặc thậm chí tăng cường khả năng nhận diện cấu trúc của các mô hình tiên tiến28.  
* **TOON (Token-Oriented Object Notation)**: Định dạng loại bỏ hoàn toàn các dấu nháy kép, dấu ngoặc nhọn và dấu ngoặc vuông, thay thế bằng cơ chế thụt lề kiểu YAML để biểu diễn phân cấp cấu trúc và sử dụng cú pháp dạng CSV cho các mảng dữ liệu đồng dạng29. TOON giúp tiết kiệm trung bình từ ![][image50] lượng token đầu vào29. Tuy nhiên, đối với các tác vụ yêu cầu mô hình phải tự tạo ra dữ liệu (output generation) trong các phiên làm việc đa bước, TOON dễ gây ra hiện tượng sụp đổ cấu trúc cú pháp nếu mô hình không được tinh chỉnh chuyên biệt29.  
* **LEAN (LLM-Efficient Adaptive Notation)**: Định dạng nén tối ưu hóa sâu được thiết kế dành riêng cho LLM30. Định dạng này chuyển đổi các mảng đối tượng có chung tập khóa thành cấu trúc một dòng tiêu đề khai báo khóa duy nhất kèm theo các dòng dữ liệu ngăn cách bằng ký tự phân tách30. Các giá trị logic true, false, null được tối giản tương ứng thành T, F, \_, và các đường dẫn lồng nhau được làm phẳng bằng ký pháp dấu chấm (dot notation)30.

Các nghiên cứu thực nghiệm quy mô lớn chỉ ra rằng, ký pháp LEAN giúp tiết kiệm trung bình tới ![][image51] số lượng token tiêu tốn trên mỗi lượt gọi API so với JSON thông thường28. Điểm đáng lưu ý nhất là độ chính xác của các mô hình không hề bị suy giảm khi sử dụng LEAN (đạt ![][image52] so với ![][image53] của JSON)28. Lý do là việc loại bỏ các ký tự rác giúp mô hình tập trung sự chú ý vào các giá trị dữ liệu cốt lõi thay vì phân tán tài nguyên tính toán vào các thẻ cú pháp hình thức28.  
Dưới đây là một module Python mẫu chuyển đổi cấu trúc JSON lồng nhau phức tạp thành định dạng LEAN tối giản trước khi truyền vào harness:

Python  
import json  
from typing import List, Dict, Any

def convert\_json\_to\_lean(json\_data: str) \-\> str:  
    """  
    Chuyển đổi một danh sách các bản ghi JSON đồng cấu trúc thành định dạng LEAN  
    nhằm tối ưu hóa số lượng token tối đa khi nạp vào LLM.  
    """  
    try:  
        data \= json.loads(json\_data)  
    except json.JSONDecodeError:  
        return json\_data  
          
    if not isinstance(data, list) or len(data) \== 0:  
        return json\_data  
          
    \# Trích xuất các trường khóa từ phần tử đầu tiên làm tiêu đề  
    headers \= list(data\[0\].keys())  
    header\_str \= f"\#\[data\](" \+ "|".join(headers) \+ ")"  
      
    rows \= \[\]  
    for item in data:  
        row\_values \= \[\]  
        for h in headers:  
            val \= item.get(h, "\_")  
            \# Chuẩn hóa các giá trị boolean và rỗng theo đặc tả LEAN  
            if val is True:  
                row\_values.append("T")  
            elif val is False:  
                row\_values.append("F")  
            elif val is None or val \== "":  
                row\_values.append("\_")  
            else:  
                \# Loại bỏ ký tự phân tách nếu tồn tại trong chuỗi giá trị  
                row\_values.append(str(val).replace("|", "/"))  
        rows.append("|".join(row\_values))  
          
    return f"{header\_str}\\n" \+ "\\n".join(rows)

## **Đề xuất Lộ trình Triển khai cho Hệ thống Harness**

Để cải tiến hệ thống harness tự build một cách an toàn mà không làm gián đoạn các luồng đo lường hiện tại, quy trình tối ưu hóa chi phí được phân chia làm ba chặng cụ thể:

### **Chặng 1: Tối ưu hóa Cấu trúc Tức thì (Quick Wins \- Độ phức tạp: Thấp)**

* **Hành động**:  
  1. Cơ cấu lại prompt template theo quy tắc phân ranh giới tĩnh-động để tận dụng tối đa Prompt Caching của các nhà cung cấp mô hình (đặc biệt là DeepSeek và OpenAI)17.  
  2. Tích hợp bộ chuyển đổi định dạng dữ liệu tự động trong harness để xuất kết quả trung gian dưới dạng YAML hoặc Markdown thay vì JSON truyền thống28.  
* **Hiệu quả tài chính**: Tiết kiệm ngay ![][image54] chi phí đầu vào đối với các luồng đánh giá tự động chạy lặp lại19.

### **Chặng 2: Nâng cấp Kiến trúc Điều phối (System Orchestration \- Độ phức tạp: Trung bình)**

* **Hành động**:  
  1. Xây dựng module quản lý lịch sử hội thoại lai (Hybrid Memory Manager) trong harness, phối hợp linh hoạt giữa cơ chế cửa sổ trượt và cơ chế tóm tắt tiến trình bằng các mô hình cực rẻ2.  
  2. Nhóm các dữ liệu đánh giá nhỏ độc lập vào các lô (Batching) có kích thước từ ![][image55] phần tử trước khi gửi yêu cầu gọi API, qua đó phân bổ đều chi phí của hệ thống hướng dẫn tĩnh22.  
* **Hiệu quả tài chính**: Giảm tới ![][image16] tổng lượng token tiêu hao trên toàn quy trình kiểm thử diện rộng22.

### **Chặng 3: Tích hợp Giải pháp Nén Chuyên sâu (Advanced Compression \- Độ phức tạp: Cao)**

* **Hành động**:  
  1. Tích hợp thư viện spaCy để thực hiện cắt tỉa cú pháp tự động (Syntactic Pruning) cho các tài liệu ngữ cảnh thô từ hệ thống RAG trước khi lưu trữ8.  
  2. Triển khai một microservice chạy mô hình LLMLingua-2 (XLM-RoBERTa-large) nội bộ trên GPU để thực hiện nén động các đoạn hội thoại dài và prompt phức tạp12.  
* **Hiệu quả tài chính**: Thu hẹp kích thước ngữ cảnh tổng thể từ ![][image8] mà không gây suy hao chất lượng kiểm thử của mô hình9.

#### **Works cited**

1. EleutherAI/lm-evaluation-harness: A framework for few-shot evaluation of language models., [https://github.com/EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)  
2. Implementing Prompt Compression to Reduce Agentic Loop Costs \- MachineLearningMastery.com, [https://machinelearningmastery.com/implementing-prompt-compression-to-reduce-agentic-loop-costs/](https://machinelearningmastery.com/implementing-prompt-compression-to-reduce-agentic-loop-costs/)  
3. Context window in AI: why every token is a budget decision \- Redis, [https://redis.io/blog/context-window-ai/](https://redis.io/blog/context-window-ai/)  
4. Prompt Compression: A Guide With Python Examples \- DataCamp, [https://www.datacamp.com/tutorial/prompt-compression](https://www.datacamp.com/tutorial/prompt-compression)  
5. Mastering Prompt Compression: A Comprehensive Guide to Techniques, Pros, Cons, and Python Implementations \- Medium, [https://medium.com/data-science-in-your-pocket/mastering-prompt-compression-a-comprehensive-guide-to-techniques-pros-cons-and-python-a6521f35bb3e](https://medium.com/data-science-in-your-pocket/mastering-prompt-compression-a-comprehensive-guide-to-techniques-pros-cons-and-python-a6521f35bb3e)  
6. Faster NLP with spaCy in Python \- Kaggle, [https://www.kaggle.com/code/ganeshn88/faster-nlp-with-spacy-in-python](https://www.kaggle.com/code/ganeshn88/faster-nlp-with-spacy-in-python)  
7. Linguistic Features · spaCy Usage Documentation, [https://spacy.io/usage/linguistic-features](https://spacy.io/usage/linguistic-features)  
8. Prompt Compression for Large Language Models: A Survey \- ACL Anthology, [https://aclanthology.org/2025.naacl-long.368.pdf](https://aclanthology.org/2025.naacl-long.368.pdf)  
9. LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression \- arXiv, [https://arxiv.org/html/2403.12968v2](https://arxiv.org/html/2403.12968v2)  
10. LLMLingua-2: Efficient Prompt Compression for LLMs \- Emergent Mind, [https://www.emergentmind.com/topics/llmlingua-2](https://www.emergentmind.com/topics/llmlingua-2)  
11. LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression, [https://www.microsoft.com/en-us/research/publication/llmlingua-2-data-distillation-for-efficient-and-faithful-task-agnostic-prompt-compression/](https://www.microsoft.com/en-us/research/publication/llmlingua-2-data-distillation-for-efficient-and-faithful-task-agnostic-prompt-compression/)  
12. PromptCompression/tenant\_adaptive\_compression\_plan.md at main \- GitHub, [https://github.com/FocusedObjective/PromptCompression/blob/main/tenant\_adaptive\_compression\_plan.md](https://github.com/FocusedObjective/PromptCompression/blob/main/tenant_adaptive_compression_plan.md)  
13. LLMLingua Series \- Microsoft Research, [https://www.microsoft.com/en-us/research/project/llmlingua/?lang=ja](https://www.microsoft.com/en-us/research/project/llmlingua/?lang=ja)  
14. LongLLMLingua Prompt Compression Guide | LlamaIndex, [https://www.llamaindex.ai/blog/longllmlingua-bye-bye-to-middle-loss-and-save-on-your-rag-costs-via-prompt-compression-54b559b9ddf7](https://www.llamaindex.ai/blog/longllmlingua-bye-bye-to-middle-loss-and-save-on-your-rag-costs-via-prompt-compression-54b559b9ddf7)  
15. Prompt Compression in the Wild: Measuring Latency, Rate Adherence, and Quality for Faster LLM Inference \- arXiv, [https://arxiv.org/html/2604.02985v1](https://arxiv.org/html/2604.02985v1)  
16. Learn Compression Target via Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression \- LLMLingua-2, [https://llmlingua.com/llmlingua2.html](https://llmlingua.com/llmlingua2.html)  
17. Prompt Caching 201 \- OpenAI Developers, [https://developers.openai.com/cookbook/examples/prompt\_caching\_201](https://developers.openai.com/cookbook/examples/prompt_caching_201)  
18. Prompt Caching for Anthropic and OpenAI Models: Building Cost-Efficient AI Systems, [https://www.digitalocean.com/blog/prompt-caching-with-digital-ocean](https://www.digitalocean.com/blog/prompt-caching-with-digital-ocean)  
19. Prompt Caching in 2026: Anthropic, OpenAI, Azure Compared \- Technspire, [https://technspire.com/blog/prompt-caching-2026-real-cost-wins](https://technspire.com/blog/prompt-caching-2026-real-cost-wins)  
20. Prompt Caching Infrastructure: Reducing LLM Costs and Latency \- Introl, [https://introl.com/blog/prompt-caching-infrastructure-llm-cost-latency-reduction-guide-2025](https://introl.com/blog/prompt-caching-infrastructure-llm-cost-latency-reduction-guide-2025)  
21. Prompt Caching Guide: How to Cut API Costs by 90% \- AI Outlooks, [https://aioutlooks.com/prompt-caching-guide/](https://aioutlooks.com/prompt-caching-guide/)  
22. Researchers waste 80% of LLM annotation costs by classifying one text at a time† \- arXiv, [https://arxiv.org/html/2604.03684v1](https://arxiv.org/html/2604.03684v1)  
23. How Batch Prompting Suppresses Overthinking in Reasoning Models \- arXiv, [https://arxiv.org/html/2511.04108v1](https://arxiv.org/html/2511.04108v1)  
24. Batching prompts sounds efficient in theory but... \- DEV Community, [https://dev.to/mininglamp/comment/39a98](https://dev.to/mininglamp/comment/39a98)  
25. Application-Layer Dual Memory for Conversational AI: Achieving Virtually Unbounded Context Without Model Modification \- arXiv, [https://arxiv.org/html/2605.20724](https://arxiv.org/html/2605.20724)  
26. Which Agent Memory Approach Is Best for Long Conversations? | developers \- Oracle Blogs, [https://blogs.oracle.com/developers/which-agent-memory-approach-is-best-for-long-conversations](https://blogs.oracle.com/developers/which-agent-memory-approach-is-best-for-long-conversations)  
27. AI Conversation History: 4 Strategies with .NET samples \- bool.dev, [https://bool.dev/blog/detail/ai-conversation-history-strategies](https://bool.dev/blog/detail/ai-conversation-history-strategies)  
28. I benchmarked LEAN vs JSON vs YAML for LLM input. LEAN uses 47% fewer tokens with higher accuracy : r/Rag \- Reddit, [https://www.reddit.com/r/Rag/comments/1sl50sq/i\_benchmarked\_lean\_vs\_json\_vs\_yaml\_for\_llm\_input/](https://www.reddit.com/r/Rag/comments/1sl50sq/i_benchmarked_lean_vs_json_vs_yaml_for_llm_input/)  
29. Notation Matters: A Benchmark Study of Token-Optimized Formats in Agentic AI Systems \- arXiv, [https://arxiv.org/pdf/2605.29676](https://arxiv.org/pdf/2605.29676)  
30. Introducing LEAN, a format that beats JSON, TOON, and ZON on token efficiency (with interactive playground) : r/LLMDevs \- Reddit, [https://www.reddit.com/r/LLMDevs/comments/1skoybj/introducing\_lean\_a\_format\_that\_beats\_json\_toon/](https://www.reddit.com/r/LLMDevs/comments/1skoybj/introducing_lean_a_format_that_beats_json_toon/)  
31. TSLN: Time-Series Lean Notation: A Novel Data Serialization Format for Token-Efficient Analysis with Large Language Models \- ResearchGate, [https://www.researchgate.net/publication/400248098\_TSLN\_Time-Series\_Lean\_Notation\_A\_Novel\_Data\_Serialization\_Format\_for\_Token-Efficient\_Analysis\_with\_Large\_Language\_Models](https://www.researchgate.net/publication/400248098_TSLN_Time-Series_Lean_Notation_A_Novel_Data_Serialization_Format_for_Token-Efficient_Analysis_with_Large_Language_Models)  
32. SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents \- arXiv, [https://arxiv.org/html/2601.16746v1](https://arxiv.org/html/2601.16746v1)  
33. LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models, [https://arxiv.org/html/2310.05736v2](https://arxiv.org/html/2310.05736v2)  
34. Prompt Caching \- LiteLLM, [https://docs.litellm.ai/docs/completion/prompt\_caching](https://docs.litellm.ai/docs/completion/prompt_caching)  
35. Prompt Caching | FastRouter.AI Docs, [https://docs.fastrouter.ai/prompt-caching](https://docs.fastrouter.ai/prompt-caching)  
36. Prompt Caching \- Optimize AI Model Costs with Smart Caching \- OpenRouter, [https://openrouter.ai/docs/guides/best-practices/prompt-caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching)  
37. DeepSeek API introduces Context Caching on Disk, cutting prices by an order of magnitude, [https://api-docs.deepseek.com/news/news0802](https://api-docs.deepseek.com/news/news0802)  
38. Anyone here successfully lowering costs with "prompt caching" and/or "batch processing"? : r/vibecoding \- Reddit, [https://www.reddit.com/r/vibecoding/comments/1qzmkfn/anyone\_here\_successfully\_lowering\_costs\_with/](https://www.reddit.com/r/vibecoding/comments/1qzmkfn/anyone_here_successfully_lowering_costs_with/)  
39. Prompt caching and TTL??? : r/SillyTavernAI \- Reddit, [https://www.reddit.com/r/SillyTavernAI/comments/1tebvn0/prompt\_caching\_and\_ttl/](https://www.reddit.com/r/SillyTavernAI/comments/1tebvn0/prompt_caching_and_ttl/)  
40. LLM API Pricing Comparison 2026: 30+ Models, Every Provider | Inference.net, [https://inference.net/content/llm-api-pricing-comparison/](https://inference.net/content/llm-api-pricing-comparison/)  
41. Prompt Chaining vs Prompt Engineering: Which Improves Efficiency? \- newline, [https://www.newline.co/@Dipen/prompt-chaining-vs-prompt-engineering-which-improves-efficiency--988a2189](https://www.newline.co/@Dipen/prompt-chaining-vs-prompt-engineering-which-improves-efficiency--988a2189)  
42. Techniques for Summarizing Agent Message History (and Why It Matters for Performance) : r/AI\_Agents \- Reddit, [https://www.reddit.com/r/AI\_Agents/comments/1n6lo58/techniques\_for\_summarizing\_agent\_message\_history/](https://www.reddit.com/r/AI_Agents/comments/1n6lo58/techniques_for_summarizing_agent_message_history/)  
43. Claude 1M Token Context Window: What It Means for AI Agents and Long-Running Tasks, [https://www.mindstudio.ai/blog/claude-1m-token-context-window-ai-agents](https://www.mindstudio.ai/blog/claude-1m-token-context-window-ai-agents)  
44. Beyond JSON: Picking the Right Format for LLM Pipelines \- Medium, [https://medium.com/@michael.hannecke/beyond-json-picking-the-right-format-for-llm-pipelines-b65f15f77f7d](https://medium.com/@michael.hannecke/beyond-json-picking-the-right-format-for-llm-pipelines-b65f15f77f7d)  
45. Which Nested Data Format Do LLMs Understand Best? JSON vs. YAML vs. XML vs. Markdown \- Improving Agents, [https://www.improvingagents.com/blog/best-nested-data-format/](https://www.improvingagents.com/blog/best-nested-data-format/)  
46. TOON Prompting: Moving Past Natural Language and JSON to Token-Optimized Data, [https://pub.towardsai.net/toon-prompting-moving-past-natural-language-and-json-to-token-optimized-data-2318aac6e8a8](https://pub.towardsai.net/toon-prompting-moving-past-natural-language-and-json-to-token-optimized-data-2318aac6e8a8)  
47. microsoft/llmlingua-2-xlm-roberta-large-meetingbank \- Hugging Face, [https://huggingface.co/microsoft/llmlingua-2-xlm-roberta-large-meetingbank](https://huggingface.co/microsoft/llmlingua-2-xlm-roberta-large-meetingbank)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACEklEQVR4Xu2YMUsdURCFR6JgiJoiRBEUUQQRhBSGgKClIlgJ0ULsBG2sFJT8BFsLBVMEi/wAQUFEcOukiIGAIKZQtBRBVBBBPce7684O+26QCAlv7weHfTP3Lcs7b5i5d0UCgUDgn1EFLUAn0DlUkV3O8AvqsMnAn5mDruLPH6Al6E26/MALaBiaNfnC0ATN2KRiVFwF3sVXGqY5hjZUfAtdQxPQx1gH4u6vUd8re1bF/ejP0Bk0n11+hJX3SdIWwCvv0xXJWN//DepUMfkJjZtcYWiEDiXf5FZxVWoNu4T2VGxN3oW6VVwJfRHXuwuJz+RFcQbWmvzvOJ/A9vBVxTuStoUWcVVcaHwms8/m9dEozictZEuc8eS1pG2BlcsKXo7jwuIzORK/yTr/ElqBxlSOxvepuBp6LwVsG89lsoVremAOQRfQD3GDsVD8jcmvTD6Be+V9FXPwcVgmw7BBfc7jHXT0BNkt5X+Hz2QOszyTv8f5UkSS3eLRVD6DzyKs7ql0ufzxmdwL3UBtJn8q7rCRRz/UbnKsWm0yyXte2eIzmRUcQYMmzy3bpskRnhzztmvM20r2nTDLBhrIHz0prirXoC6oXrI9jpW5LW5rRnjlCZF918LdBWXhzoMvjthrCdtHT7ocIBxwI+IOJwNmLaFZ3B9Simlxw29dskMx8ATeiv8VJ+EfwZdGdXYhEAgECso93Yp09PCYaNsAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEcAAAAWCAYAAACSYoFNAAABqUlEQVR4Xu2YvytGURjHH6EoZSNFUUyUgZRNokxKSMmmWEwUsVv8ARQWgywWZfBjoAzKgmI0ECsLAwO+3/ec+95zj+t27/R2T+dTn+F5nvveOk/n131FPB5PiamEX/AFjsOyaLlID7yzky7DRizCfh2/wvWwXGQEvsMFu+ACjXDeToIW+AyrdDwHv+ExnIZjcAX+wBNYo5/LPTuiBrUF3+BStFxgVdQzAQ3wyohJHZyycs7AAT9KfHO25W9zboy4Am6I2pecJKk5A6KWUbAJD8OzsCy3cNSInSOpOdxDuJc06/hUwiXE2cJZw9njLEnNCZiEm7Bax+3wISwXNuw+2G3knCBNc2w4m5aNmMf4BbwWdfI5Q9bm8LJHCZfUHuwKy3JpxTb38Cmla7Bc/aw0ZGlOLTw34npRy4vvCNiFs0aca7I0h41oNWLOkA+JNoeXwjTvygVpm8O9ZCImxxu0PXPibtu5gsc0BzUDP+EB7NA5e53z2OZpZV/2eHodwU4jxxt0rxE7D7+2B+2khhdELq19eAjbomX3GZL//6ogTaI2YX6Mejwej8kvz4RP/GBLkUoAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAAWCAYAAACcy/8iAAAAl0lEQVR4Xu3VoQ0CQRRF0U8IColCojZBUACSCjAkVIKhgjW0QAcUQAOUgEaCwSAwBO5kUK8AEv6+k1yzT85OJsLMzOyvrWmmH7Np6EV7HbLp0YkeNJItjSHd6ExL2dJpo57mnPqypbKlN010yGxMTzpGvbudUp6ey7eBbGmVO7ygO21kS21KB9pF/e07pTxZV1rpYGb2Cx8hehHn8tWOKQAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACIUlEQVR4Xu2YPUsdURCGRzQQQRQSEhEUGz8QhAgGQcFORRALRSwkhSBoIxYJRJLOMn8gAS3EwloEbbTQ2kYFK9FC0cpCECPYqO/rOevOnuzHvVXk7nngwT2zu1zu3HHO7Ip4PB7Pf+MN/AUv4Q0si56OcARb3aAnm+/wzh53wd/wfXj6mXI4Ar858dxQD7+6QcsQnIHNsA42wm04p665gJtq/QDv4RQcs57AR1ilrit5VsR86SV4Deejp18YFXNdICu2MnKFiev792CbWpND+MWJ5QZW55kkJ3lYTKJZjZ/F9F8XN8kHsFOtK+CyxN+bCwpJcta/ONvDqlrvSHgP2wurONcUmuS3cED+3dDIFjy1xzUStgVWLiv4j13nlkKSzCqttuseeCWmdWjYpxfhhIox8b1qzR8qqeWUNFlJ7hNTnQGcgdmDWb1psPp/SDgzc0q5hftiNsZckZXkOIJJIwnOysdqzY3vr4SbYa06juMTPC9CzuCvmrQkc35es381WUnelehDB5PKz+BnEVY3Z+/ckJbkn2KSOe7EGeNEEUc/bHJirFqdZBL3eSVLWpIHxTypabhpJfVkVnzcuMa4W8lJT5glBTcmfulpMY/A67AdfpSwxzGhnBje2TWTMymmD3bYmIbXUhdOHnxxxF5L2D66w9Me0gIXxLwIch+XAxrEtIokZsVsfhsS3RQ9RfBB0l9xEv4QfGkUzNwej8eTd54ATbFqBrgce/UAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADkAAAAWCAYAAAB64jRmAAAAm0lEQVR4XmNgGAWjYBSMglEwCugGIoBYD11wOAB1IP4LxPPRJYYDMAfi40D8BYiF0eSGNOAG4ldAfB2IWdHkhgXoZIDEmhUQM6PJDXlQDcT/gVgRXWK4AUkg/gHEu4CYEU1uWAJQNfEQSg/LfAkDoDx5CojfA3EZmtywAqBkqwXE64C4jwGSpIc9AFUvL4E4FF1iFIyCUTAKiAUArvwR0qb2pa0AAAAASUVORK5CYII=>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGcAAAAWCAYAAADdP4KdAAACDklEQVR4Xu2YPUgdQRSFr0hAUbAQA4JgiFgIamMRSxELBbUIgilSa4qk0UKw0tYibQpBsbASC0FtbB6YykAKURG7pIgQCIKQQBI1Occ7o3eX53sL/oDs/eBj2bszu485b2d2V8RxHMdxHKcITXAiXQxMwtewGTbCVvgZ9ttGzt2yBP/BeXgCp5KHr5gWbRf9DisTLZx7g3fDF7k5HNaH4AhsEw/mQckSzkNRkS7knazh1MKesLUMwK/BTfgCrsNz+FF0wHm37YbaCmy57KlUw3ei/b/BX/AIdpk2uSVLOLOig8iBHoV7og8IkZei69EFrAs1tl2EZ6L9I59E20ZORdc/y4F4OJeUC+cNfGL2eedwcD+YGtekGI6F5zyGz02tIMlwfooG1mBqC7DD7OeWcuEUIz65RWI4HGgLz1mQ5FTIfduXd92fUIsOSun1J06jWXzUj/ylwumE23I9VUVuCofnsWQJh/A3cOrjmsRj3A4nWuSUUuEsiw5Wd6rO2g+zf5twuL7YaY/wXaqQquWSUuG8hTupWr3o4BZbc7i4W7KEw6mQ17Hsw41ULVdwwBjMGPwN12B7qMUXTU5nW6JPaoQPBjOiCzg/+RCe573ogP8N9SrRzzyrosH3ivZ9Cg9DW16LQTMcfqHoE4VrDc/zKuw7ZeC7yxwch8+Sh25NTdjyD8E/BgN0HMdxHOee+Q/DzYUxu99wYgAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACXklEQVR4Xu2YTahOURSGl1DkbyBJkYhkIIoUMUNKBoSBDJSBiQwIGRqaGrhlYmQoE0pSzpgBSikxIIZSQkl+3sfe+571Lee7uiM6Zz/1dr619rn3dt+zWmudz6xSqVT+GbOly9I76aM0Y/R4hGfSupis/J3z0pf8eat0VVrcHv9mpnRAOhvyvWaf9FhaKy2TVkrHpNP+pswRSxX4M18xzPNWuuPiH9JX6YR0KOulpZ+f7+7rPQct/dNFVOK5kTsSVN5Fa1sAV+73FUl8wcUPpfUuhqeWHuKg2C89srbS6KuRVZaqNBr2WXru4mjyE2mzi2dJ1637b/QaTG5iMnDFkoELQv5VzhdoDzdc/MDatkAboooHSTF5jqVhFQcV0Ge7+miT86WF3LNkPCyyti1QuVTwRI4HByZj1MIcb5c+SFsm72jNHGeyz8+VrklHXQ7jd7qYB8rvH0zb2CXddDFVSdVRlcW8xv40c6q8hzM/MNlmPlnaaBiMg6VUdxliTY6jmSU/L+QLtJ8XLmbwMSzLMFzqPnexUXozDcWV8r/hVpYnmsww6zKZrYT8OBobXfEw9bWlfRyo7pPtcX/BpGgU5rIp0Epgh/RNWj15R+K9pZeNLnZLa0KOqvUmg1/5egtvYBtczDCisn1P5tpIe3Nc4EHcDTlYbt3rGvlYyWfa4/7CJuAH33Hpu7TJ5YDKvG9pNQOubCH03Qi/E0XYPPjiiF4LtI9t7XG/oaIuWTKGt7pxA4QBd9jSy8mecFZYYemBjOOUpeF320aHYmUaLLGpv+IEHgRfGpXdvFKpVIbOLxjTgMVb+R5gAAAAAElFTkSuQmCC>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE4AAAAYCAYAAABUfcv3AAACOUlEQVR4Xu2XP0hcQRDGR9RCFGwVUtqkCYIB/2CRwjSGNBoR0eIgBBs7wZB0tsFGCAkEmxSpAjY2giFcFAQVlICSXiIWKdJoYaHx+9j3cN743t1yx+Jh9gcf3M6+u7c7OzM7JxKJRCL/B93QX+gftAONZ6cbng1oRtw+qFloP/NEAI6gBTWm0y6hT1CrsjcyPHCtKag580QA+KIDNW6D1qELaFDZG5k16Dn0Anpo5oKRnpKGi6DttbFbXkI/rVGxBG1aYwA+W0MBTF+dXZZecdHqxTD01NjeinMca0UlmA5vJP+Umea70AM7EYDUcU8SFdED/ZL8EvQY+g012Qlf6ETWOJ6M74/MQ6dqvAJ9V+PQ8JAXk89cM9d/eDN9C2bJRzXm2ifFf7+5MEq4kLxTKYIvnIOGoHboG9SZeSIsy5Jdb1ncHlqUTcMs2BNXz0ekzi6CL+YplKR2z3MxV9boCW/3Y0+9S75TBGszHcdaXQT3yLXWXYOZmmdq3JHIly5xKToBjZm5kDyCPkg2wqs5jk4rQaPQV6kjOxiqtsBvSfGLLbZmMGVZN2qNXF/4+1+gc2hA2XlZ0HF2T4Tf4dp4GaTwwBl5PHxv6DT2bNPi+iBGHpvfP1Cfeq4I3lRsO2xN5MJKEt55rK38t6Bh25FX49IugG2HJi1TP4y9IrbrTlWW6qlKR7+yRgVP/L01BmBb3F9GRtoJtCr50cNLpFJ7RAc+s8b7DCOpX1ymsPcMHeWRSCQSiUQid8k1ZhttwHeqYI0AAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAAAWCAYAAAAYTRgMAAACVElEQVR4Xu2YPWgUURSFr0hAUBNFEQRBolgIBgOKQpAUkoSI2IhaWdja2IQgKdNaCIqVjZVVCKkEoxZTBgIGxL9Ci4SghYiNCv57Tt69mTtvd9ldVlyU+8FhuOe92V3m7PsbkSAIgiAIgn+Y09ASdADaDe2FLkJXfCflAvQU+qXXjdXmoBuclRSI6TM0WemRmICmoA1a88r+9IMucgZahM6peqrNa/RDq9DBzP8Evci84C/DAIvczLgpabRtzfzX6v9JOLJjam4DC3ATdAzaUWlN3JMU1JbML9TnQz8Frah6oePQR+gHNKx9GMwT9Wag/VLCNq6x7ySN9nnolWsPGsAAGQIfOhmCPkBH13uUQTUK0HxbTx9CferZWvkdmlaPcNr2o5ejuXD1dkl9giaMQLOu5gO/Az2QMphCWgvQ/gzj1kGh9xba57xCfWMZeuNq/o4brg7awIK4qnWhdaMAN2tt9x2xDgq9Qqr3s/YBcsRz+qRHfZX6RxnPMymn7Wa6pvf8d8ypPHmAd7XOA8ynQbuP50lPKwESTuMLksKzIIMm1HtQDO6npOmVnIC+SXUKJO+hL67uJMDnkr7H4GbqsdR+VpDBnd6Aq3kO5Ij0ayCvhdSubQz5vqstwMPOI60EyDXwlqu5K+bud6fzgjrcluom5pKkbf6g88go9EjK3SWv3K3y6EEYznVJoVyG9kDbJL2io8eATkr6g+yCXqp/SNJoYzu/19702G44aAE+NG7xGSbftjQ6SHOzcl7SwX4sa+sUe0nAMDlt1nsjFARBEARBIL8BqvuWql3wED4AAAAASUVORK5CYII=>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACaklEQVR4Xu2YTcgOURTHj1Dkq0hS5CMlWVgQKXZIWflcyM7CxooiayuWEoVSys6SkpQpO+/ipZTysSCykJRQUvj/3nuvOXPfeUbvimbur/7Nc869z7P4z3nOuTNmhUKh8M+YKZ2T3kmfpWnN5QZPpbV5svB3Tknf4ufN0iVpUb08wXRpr3Qyyw+CZdJV6Zf0SZrdXJ7gkIUKZA9XDPO8le64+Kf0XToqHYh6aeH7c92+3sNfmgq8YuHvPkO6YcEwjE9QeWesbgFcMctXJPFpFz+S1rkYnkhHslzv2W6h2pbEeI50X3ovrY65VRZMzw37Kj1zcW7yY2mji7mB1y3czEGBwZjTxQULe+Zl+Vcxn6A93HTxA6vbwgoLVTxIMImKZNKft2DolsaO0Gfb+mgV86mF3LNgPCywui1QuVTw5RgPCkzDJLQy5jDsonQ2fobKuk32eQYm/f2wy2E8bSkxS9pkA2kb3mTPDgvVnfppZZPN7Mp7WPMDc4/0RRq3MBh7D4MotQsP5pK/ZWFPFePczJRnWLbBWfm5i/ktf/MYtn4w5myQ3kxB+ZHyv6HL5MqCsQyzNpPHYn4UlTWPeJj6WloaY6r7WL3cXz5aOBV4ksnHY7xN+mH1kS7BdzmdtLFTWpPl+F1vMvgjX2+5ZpOrcZ/0QloeYyq4knanDRFuzt0sBzzEtB3XyOeVfKJe7i/rpQ/xCgulh9L+PzsCVCYPKRzNgCuP3/TdHE4XKIeTBy+O6LVA+9haL/efXRbOyAdt9CAjzzr72N8G1c8NGQUtiBlw25pDsTAFFlv3K07gRvDSaH6+UCgUCgPlNy3+h9NZEHfDAAAAAElFTkSuQmCC>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEUAAAAWCAYAAACWl1FwAAABKklEQVR4Xu2WsUoDQRCGf0ksJEWCjQpCmjQphICSQvApJKQN2KZL5TtYpEsTEPE9wmFrIbGxVgRRCKlsBDX/sHfnZpWQBQkMmQ++Yne2uPnZmzvAMAxjNVRSjZQmndKrsLCubNDvVAsl5YROYKHk9OklTbB8KGd0HG56bNIbKJ5P0lwVcaEU6DmthwW4QAZ0PyxooAj38NKEkGD5UDJ69MVbb9ER3fb2VHFK77x1gvhQZEB36TEt0WtanjuhCLkdMkukqYwE8aFk3NIv2g4Lmjikb/TJ8xMulA96Tw/y04vZpUPaoq9BTT2PiL8pMqRlLvnIjOkEe2qJDaVGL/AzqDOO6DPmX011yL/EHn2HC0X+L3bwu1kfCeQB7tP8Fw24Aaw6GMMwDOMfmQFARziG4LDy/AAAAABJRU5ErkJggg==>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKcAAAAWCAYAAAClgIw8AAAEAklEQVR4Xu2ay6tNURzHv0KRV94puroDygAlDE0oEgOE/AXymFBkou7AgIGBiZJHGHgOFJJH2jEgSilSpBAphQkKefy+d63lrP07a++797n7OOeeuz717e691jp7nbPW9/zWb61zgUiVDBE9FM3XFZFIK1kk+iw6KBqp6iKRljFd9Ez0AyZ6RiJtwyjRWF0YifgMFU1EfvQaDmOmSKQXmoZqJs9FF2HMd0S0DPV9ToFZfrkMl4WGPyW6pSuEcaKtiKZva+aKVuhCYZ7ormiLaF1ARTcQe0XXdaHlt2ipvZ4q+il6h1of50S/RKttmzIsED0Q/REl6apebsPUXdMVkeaxUhcESGAm/TiMIValag07YCYvS3nLMJ/3SXQW2eboFr0WTfPKDnnXZLPoviori+6/S/RENMHe8y/vWf4/6YEJAIOK3bogB0aXrwibk0bhUkrz+AY6D7MEF0Wbw8GJ0eY86V2Tl6LFqqwI/Dz6y+T64nK+sda0l022/H+SIDzuHU0V5mQ0YS6oYU7Is8EyZJlzhOibaKG9H43a8s2ovAvVGCar/1aToH7cO54qzBmCyx43JmXJMwdTiz32ei3Mrp0wWjJqNsJ20SuYZ19FuH9uwJjbuqi6H7VjJf5S9MaKkXY2TIrC561H/YatURIUG/eOolnm5GH1cl1YgJA5fDj5B+xfwqjJ1IEGcvfcsHHDlAejLHflfmTnpk33f9iW+TnzUVvmYDRnVH+KdC6qn9UfEhQb946iGebkxHOiJumKApSdUC7tM+01+70guiT6iPxNGDdP2nRE9/8dZhPoswam3Xh778Zl278WBrZh7loFCfoe9wELlz23/Pj6EiijHpmXpShizmGiMyhneh9tjjy40fI3WzTSCe+e19p8jvdIRz+H7p/3lB4fapZtkzUujZiTXxrdD8U0gemCLr+JWnrTcZQxUdYk+HTDTHxemzy0OfJ4jPRhO1/rf557yI7e/BxFzdmXwdy48K9PkdcWJUHjYzpgqdqc+2Amxe2qNdx15+WD2hwhmBteRn1U1Oa8g/TRk08C036GKmcZ/yXOwWgcMjFPCybb62jOJlG1OXn2yEnRE+XgDp71nNwQRcy5E+E22pxMTbK+CBtgfnE6jdpPkjQ7n/HWNYJJG1imf+Fi3umOrty46F/Oojn7SRFzOsNpJUibzOWbrMv6NeMKjCnY1sHJ1c920hNCQ/BMU0dNckP0wl53wZyz5sFncOlnP4yyc0QfYJ7vQ2NyN852rGcfS2wd359+zxxT/z4UVcuSoH4sOp4i5iwDc8AehM1TBXy/Ooo52DeX5GMwZ5f+F6C/8LyS/1TCNKGqs8syJBiE5nTng5H2Zgxa86WIRCKRSFvxF+bjE+V0Pw6wAAAAAElFTkSuQmCC>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHkAAAAWCAYAAADkWDPGAAACi0lEQVR4Xu2YzctNURjFl6TId0Sk9DKhlAFRkoGQCQPFxEQpH6UUAzHiHzAweQslAxNloBAxuMlAmfqKFFIGkhIK+VjrPnvf85zj3u3yvr2Xen61Onevvc8+p7PO2R8XCIIgCIIgCAbGAupQ03TsoO5TP9JxfL26zSTqOazNHWodNc43CMae87BAzlDvqCP16g6HqaOoAtNR58nPDFPfXXkCdZH65rxggMyjXqB7yEPUK2ppw/9IPXLlz9QDVxZbYS+DvvBgwJRCPgULamrDf5Z8MTH9vlBVt1lOvad2NvyRElPAX1AK+SoswCkNv5V8PfDZ6beGf0/u91gq36JeUteoadQV6gOq+VvzvOZ+DfHyF9tpHVT/mHpDfaJuUFtqLYKelEJuoRyyfJ1fCtn722Bz903nnYOdfwLVVzozeXtTeS5s9PD3oTYRcp+MZcgKRSFvdp6uq/MXOU/9ysv3lPta0mlhL8QGVw4KjCTkyfh9yGedp5C1aFvhvByyv0YzZLEyeVlf0H0rl9GaQNNDvyr19d9TClmLqWYA4l7yhRZl3ULWl/ka9X4Vsq6la2ZKIef5PHOQupvqJL+NCwqUQl5LfUV9KBVvYdumjB64gvdoKNXQPOS8Pw05vzhq/7CqbjMLv/YV9KAUsh52C/U5VCi86678FPaHiucALCjNnRmFrG2VhtJMvyHrHn1f2rppb67VfdCDvGjaA/sqL1PLqDmoz08bYduf6amsowJd1WkB7IOFon+6xELqSVJG3knYyLAfFtIM6hLs3PWwa0vaUsm7Dbun+bCQd6EKeg11PP0ORgEtsLbD/hzZ1Kjz7KZOU6sxugsZ9aW5XwFrmNaWKr9QQRAEQRAE/yw/ASmfquaIXJxjAAAAAElFTkSuQmCC>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACaElEQVR4Xu2YTehNURTFl1Dks+QvRSIlIwMfpZghZSQfScrAwMSIIkMZmcmAkjIy+5cBSlLuSGKAUkoUYiglFPKxln2Os+92PYzo3vOr1X17n/N6te65e+93gUqlUvlnTKZOUC+pN9SE9nKLB9SymKz8nsPU+/R5DXWamlOWvzOR2kodCvneM5N6Sn2lblG7W6uFnbATqH26yjDPC+qKi79QH6h91Pakx7DvT3f7es8l6jnKo70WZsw5alLeBDt5R1H26Sqz/IlUfMTFt6nlLhb3qT0h13uewczJZsxPOUmfxWLYKY2GvaMeujiafI9a6WLdtPOw2j0oFlF7XbwaVlcvUlNS7hTMwBl5U+JJymdUHi64+AZKWdDv6BRXyHGYcWpcGdXZrjrapHwuIddgxotZKGVBJ1cn+EyKB8tbmGE3qQVhrcFok31+KnUW7eYp49e7WE/IKgywbIzBavBd6iPaBjT42cxReY/WfMPcAruh+h01xkEiM1RXZd6ulGtSHM3M+Wkhn1HJeeRiNT41y9wM57nPXayATT5/qjhS/jfMTvJoQpB54zBjsunR5Dsp/ysatEc8meqnFt3Q/WW5n8g0mRSNytOEZmWxjvpELfmxw3gFm6m72EgtDTmdWm+y8CNfL8l/KLzJalxXqc8wo4RuRkNtTnFGI5v2RtQ4u8Y15eNJPliW+8tr6qSLt8EM1nuI3KyEDL8OG82ErvquH/Uymi6kiG6gXhyp1gqVD/3DHARqGMdgxmxA+RMSUYPbASsnm8JaZiHKE9DFAVjzu4x2U6z8BXMx+hWn0I3QSyO9mKpUKpUK8A1qGoXcim8fSwAAAABJRU5ErkJggg==>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAWCAYAAADafVyIAAABtklEQVR4Xu2UzStFQRiHX6GIkg0phWIhS1IWSkJK2fgq2VnY2CnFVv4FSkoWsrG04FJuWSgWKEsWiqxQYkM+fr/5OHfOew+XsrxPPffc951z5p2ZM2dE8vwzxfAV3sIRWBBvjmiHFzqZC3Y2C7td/ACXMs0RhfAZziQ1sOqnu466nKcB3sASF0/DD7gLJ+EwnIeXMAXL3X0GVmPHfsq8LricZ1HFNfA4iEkVPFc5A0d2r3Kt8AVWu3hVsgucBTFZhmsqZ+CDhyrHjq/Ejpz0iF0SP8tBeOD+kzo4FMQRXFMWSKs815C5DbGdMuba1rv2PTjh/nN3ceRFLo7BB38qQMMXNg5XYKmLW8TOtDO6Q6QLtvngrwU0nNWcZJZuQOxyn8JaJnIV2Idl8aYIflDUsyl2Y3iO+MPKSQUq4QlcV3lPhWQ/w6W6DmK+P8MbvAsaSLPYrduh8h521qhyHH1YgB+eIS12C4b0u5x/mSFc2zGdFPs9Jc6gF76LnTbhlWv/6G8I4JbkLuJVswOfglh/6eaE5AHWJ8kdEJ5THFASfJ88o7bgNmyKN/8OLt13x7RnSuwBmCc3XwFwWgPyf5DOAAAAAElFTkSuQmCC>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAACP0lEQVR4Xu2VPUicQRCGR1RQ4g9okQgGUWyso6m0VBQrQQOK2FhoISkUEmJlbxMsDASDlQgSsFEINn61FokgKKKFIFiJCCoG8WdeZ/d2dvwOLoWQ4nvg5W7f3dud3Z3ZI8r4f6hjlVnTUMkqtuZL8Yl17b6/Z82zakP3EwimjzVl/FQweJf14D5H4u4cHygeZ3d8wlpX7XvWX9Yoq9/pkOT3FWpcKoh8y3jY7VdWkfIw7ovy8IkF9M7R/qzamLdFtcEOa9h4qWyzZo2HRY9Yr127keQ07CJXrD3VtoH9Yb1T7RLWIqtUeXlBAJiwSnnIi1UKCTxHMgYJq/G/9eDqllR7k8KVNZCcVsEsk0x+wRok2c0MyXV6kDdpeZE431/vBkmwoJrClWFOnNQ31y6YNyQLQNj1dNydCyBfYNovZ31nDSkPwXaoNm6ilQq40jaSasGp+QDrVX/ivEICs6BPF00v65L1m54XXcQ5yTF7fJBYcMJ5iWvbALz/yvgepMOBaiP5UTC+IFBcujgiblntxkN+YMGfJJMhodMCQ0XDz0dC8XOCQI5J/hkATnEsdAew6CmryXaQPA8L7jsCxwbsuDOSBzSNTlaz8XA6OjCgn5cI7HjcmswNyeQAJ5WwunO9Agrll/EA8jPtaYBvT2wydMfUsFZI8uoHa59kQVsxmAT5gYk/us+eaEQAQTVY03FHckqYD/+tqOK8+LtGmePtsX+8HiT5AMmD22X6PG8pnHQaKChscI3iwsjIyMj4Vx4BLMt8CPI2oRYAAAAASUVORK5CYII=>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAWCAYAAADafVyIAAABsElEQVR4Xu2UvytGYRTHj1AU2ZRSKAYZSSlKopRYkMKgDBabInb/AiVlksVowDtQBrGg2BgUKyUGyo/v9z7nue+5z3vrvoPx/dSn7jn3uc/vc0VK/DOV8As+w0lYlnwd0w1vw2QW7GwZDmj8Ajfyr2PK4TtcCl80wFf4Cy/guLjGnhb4BKs0XoQ/8AjOwwm4Bu/hMazRdhF34mbnYeff4gbjtpB1jT2c0KWJST28CXIR/PDKxNXwUPM9mtvW2MMBrk1MNuFOkIvgh/ZjMqq5FY0HxW2JP9gxeKLPpEncylPphUNBjvvJARY05p5yb5s1zsFZfeY2cuYVGmfCwfwZhFdxGm6J20bSAR9gX9xCpB92mbgAHh47555mwVWtSn4iI/BM3Jk2+kYeLpWdzknhzNNgQVHPHvww8bl5juBVZZFYEvfZUAdPgxy36tHEu+Y5ugHtNgFqxd2mNNhZa5Dj7O0AvCgR7PwTzoirSK6EB7kPO30jA/d2KkyKq/TUFfhfRJosKAvPiYP7CrewON9MHFZ6UfAvGdaMhxeD/yiu/AC2JV8Xx7Bk3zAWJ3+AJbL5AxHUVisOSk3pAAAAAElFTkSuQmCC>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGcAAAAWCAYAAADdP4KdAAACPUlEQVR4Xu2YPWhUURCFR1RQVET8gYAiGCwErSxESCUKBmIKFSLYCBam0FbBztbCShAsEqyNXRJSLmgTLQQhItqoBAUbQWIgxr9zdmbYeXcXXPClCG8+ODxm3r1vlzl75963IkmSJEmSJIEB6Cv0B5qHLkAbKyOUG9B76Bf0DNpQuZvUzgJ0M8Q0hsWnUZsttwl6AI35ILvHcaMhl9QMTXgZ4q3QnOVPWo7XFWiPDzI4hmOTNYIFpiLnLHfL4hmLyzb2zfJ1U35OYxmCzhS526JFv2YxW18vEz5IJz8MfTTNQiegaanuT9zHXlnuMTTYnqlwxXJP4/xP0DL0FjoexjQeGuV7jv+CowmRMn/e4t/QTsvxGZPQT+iO5cgLqc7lKnwUYvJa0pwKz0WLxgOAU5rglHlvhzQnwvb4GToUci2pzv0uatjekJuAjoW4sfD0RUOuSHfPL01wyrybw0JHaE4L2h5yjMtV98NyrhHp/i4Rb6P96KzNWZfwOL1U5LyYT6W3OVwNvcyhaZF+zCF832Lr87aaR3XRd5sjRW6HaLHJZdFi7ercbsP2tRji/zGH+0tse+SL6LjGQmP4DkMDLoquoIfQlHQ24wPQO+ioxQ6Lez/Ebg4390g/5rAVXg8x4SmRx/jG4n/b9BLbjDMuapr/a3BQ9KjLK2Hh74nOW4X2Q1ugw9AT0dV0SnT+PuiNjaXhu0XN4Xc5LQr3Gj7nksXJP2ARr0J3Rd9j6mSbXfkuxB8FDUySJEmSZI35CwlwoEYoMRdiAAAAAElFTkSuQmCC>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACU0lEQVR4Xu2YzctNcRDHRyjytpCkSKRkZUFKsSQlC3lZYKEsbKwo4j+wtaBsrPwHlKScssICRUosiJWkhJK8zOeZ3zxnztzj5VnROb9Pfbt35ndut75n7sycK1KpVCr/jLmq86o3qg+qWd3jDo9V63Oy8mdOqz6X91tUF1VL2+MpZqv2qk6l/OBZoXqv+qG6q9rXPZ7moFgFch2vGBZ5rboe4u+qL6pjqv1Fz8U+vzBcN3ieiFWgg8HfVJfFfv4OlXdW2hbAK2bFiiQ+E+J7qg0hhkeqIyk3eDDmQYjnq26IVeDWklsjVqXZsE+qpyHOJj9UbQrxHNUV6d68UYAxKLKn5NywCyVeNH2F8aLkHdrD1RDflrYtrBar4lGyTbUj5c6JmXe8xPTZvj7alLy3kJtixsMSadsClUsFXyrx6MFwejJ92s1r5Pcmxzzthn5+KOQwfnuI56k2ywjbhsOwwrhoQFNyf2NyhrM4MHerPorNAb5rVGAqP+ejMvkQ0Ui/mZ5fkPIOu/KzEDP4GJY+DJeH931sVL2agfJK+d9Be6DCHAx1UxlmfSbfL/lf0Uh3xcPUl2J7OXAzve8PHnbjvJ7dEdsygOH4VbW2PZ7indiq1we9fV3KUbXRZIgr32DBYIw6LPZERkUzuN5K+1OmghvVrhI7rGzs1JmV0r+ukc+VfLI9Hi7+OJ2VK47KvCW2mgGvfJa+m+EmoQybB38c0WuB9uEPPJUCA+6A2MPJznTmrJLJvTtyQmz4XZPuUKzMgGUyuZ1kuBH8abQ4H1QqlcpI+QmlNIQxOmMHtgAAAABJRU5ErkJggg==>

[image20]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAWCAYAAACPHL/WAAAB+0lEQVR4Xu2WzytFQRTHj1CUsvArRUo2spBIWVjakIVYICsWUlYUf4GFpQ1lIwv/AcLGW1v4UVZiQWQpQrHA92vm9uaed++77/Xeu6v7qW9v5py5d+bcOXPmiSQkJCgqoXXoCXqDyvxuH9faEDc12hDACvRp2/3QJlSXdv9TDo1By8peEHzpLHSlHVl4hTagSWhCqdOOeYQObJv8QF/QsaTH3kK/ksMHWtCGAD6gd+hQzEvv/e5QmsSMD1ObHcf2qm2TM0kH68GPOKNsgexqQxY4aT4BcVHDULOVdzYGoQdvkGQGdAn1Ov0KaEfMWYuklAFNSeYBr4a2xb84ptie0z+VdGpxF/NJ8ZIGpGFwLAD6wJ9Ad7ZdK/7U4s5sOf1I4gwoBR1po8XbuWnH1iUmPT2qoD6nH0icAfHZeW0MgSnHnfNSdkRMYbrwBnBLeRC1vgNs1Ll5zEchAQ2IeY7FIQreRTf2l7AosNK6hSKUuHZoTUzKRd4jYsa5FyjLf64fo6gBcbG8fDXt0LOYSqarnmYI6lA27kzsAfVAL2IqElPEhQtiykTN1SLBJZr2ogbUKOZlPKQMiIvjJO4ES9aXksy0GhXji5qLVY7SsALyT2u3dgQRNUkxYBqOQ/Xa4dAqJt3CWBTzIfe1QxNHQLnQINHni0HPaWNCQon5A/K7elzljjv7AAAAAElFTkSuQmCC>

[image21]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAYCAYAAAB9ejRwAAABq0lEQVR4Xu2VPSiFYRTHj5CE5GOgSGJRBmWQMhiYxIAyWJTBwqSIJLNZlCxm7igmCwuLhQwGlDJJZDH4+P8958nznnu5H927vb/69XbOee77nN7n44rExBSORvgMv+AZHIPFkRGOOXgHP+ApLIpU88gVXAhiNsRJ2WCp5krgFpzwg7TGcSNBLm9w8osgLodHmu/VHJ/vsN4PUjiGY/mbvMIX05BhzS1qfKCxXa5XzU8GuX74EMSWWXgJ22whpA8OmtyyuMlmNOYS28bJvbg8x3vYOJd5IMh5WLuFXbaQDjbo95T/Mn5yi8/v2gIYhU9BvASvgzgrzsVNxI3tyaUpMiTuq5WJa6glWk4PTxMbmZLkvZOuqR1bCEhI6v2YEbwW3kyuUp8nkrqpR4keCEsFPBa3v+Yly8Z4N3WYXJW4U0h4ujh5zW/5h09xJ63V5Mmh6mkXt4T+7vsXNsQ7iBOPi/ti23AfduuYZngDOzX2sNENSf4CtXAPVps899SaZNAYX/yXfvkI/3Z4KnnRrsAXSX20e+CqTQY0wE3YZAu5Ugen4bq4yWNiYmIKyTerxWEBcP5VyAAAAABJRU5ErkJggg==>

[image22]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAkkAAABcCAYAAAB6BCE1AAASgElEQVR4Xu3de6wtV13A8R9BEsE3Tx/IvRcEIhaVQiGimAPSghSEIFEaCm0kBEJKeAW1jYTbkP4BRmMMBqLGmzYp0AYfpFSegRESQf0DaIAmiOFCaAkQMJLaCEZhvl3z66y9zsw+e5973uf7SVZ65rFnZs+sx2+tWfs2QpIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSTo6LuzT//XpN9sNkiRJx9WJPn2+T9/r0wOabZIkScfSPfr0v316ZZ/u2WyTJEk6tu7Vp2dGCZYkSZIk6dC6uE+faFdqSx/s0/3alToSntGnn2tXavf8UGweXeF11H2Gv9leW/aqin1f1648QH62XXGIMBL2oD5d1KdnN9sOAvIQlfLj+/S8ZpuOL/LFTzWJfEx+XsVXo+QpredTUe61jh7K1K1R5thqD/x4lML0gSgTmkmP6dMPD9tp+Pg1GOufPuw7J/f7gXbDPrt3n/66T//Up//p03MXN98tv/NO+Y8o9+NXmvXX9+nGYdt/Rwk8ube8Dpzzg316cJ/+P8pn1jF3HVNovNqgeRV8hwf26UtRziWB+uVpfbqzT9dFycMZLD08Sl4mv/xYfmDA8oeilF2tzyDpaPuFPn2jT29sN2j3MHx3e5QK60nNtq/H1g+DwOq7fXpRu+EAIEAiUKDxvyJKxTwVCFzVrjhHGZw8tln/4uG//xZl+3/26Qt9OnX3HvO49u0GSe11TLkgzi1Y7MIgSYvolJAnpjondA4I/P+gWf+yKJ0ubY9B0tFG+/VnsX5boHN0aZTK7KMx9uwYWfjXWP5+O3t9NLAH0cei9GBB5vqtPv30uPnu9Yzw7KTH9enPY3NAlq8P6CW/oU+39ekp4+althMkzV3HFBoygyTtJPIeeeLn2w1RAnfyM/VH/WqfeUjORdo+g6SjL8vOKvW6dhDDeDm6QWDBu8/j8BAyQNxvX+zTq9qVle0ESavK0USDJO0k5hXN5YmXRtn2jhhf01Pf8M91/FrupLUZJB0P1/Tp+e1K7T4qLdJf9ekzzbYWc2V+v09/2adHxHxAxXq2sx/7bzVxk+2MgLw5yr+O/aMxFnpGtfj7N2Kcs8D+Oc+hnRO1EeWcL4/pa2SZoHCuIp/DOQkqGRniPjwyyvX+6rCd6yHQvO+wnPMvSM8a1vGaIdd1w395PTZnKkjiHHdE+ezZPr0iFudytNcxhxFEjrEsSGLy+2VRGreTi5vu0sXq95H7xwja1X369WY9k3u5r4w+8HwY+duI5dfW4jjc5xwFZZmJ7+2PEQ4TnivlIssP+e6gf6fM31PeF2XbhdW6+/fpKzGO/ia+K3l5Y1jmHjwnxvKXyC88c+oCpg4w0s09an90wj50jrJeaJEHKc9sPxVjmU2cn+3k37o+q6/zZ6LkYc6/XZSRqfMss50gift2MsY6Muvs3fjBS9bvddmkDjiX+3TQkS82YvE78ndd962LtpHpJNpjT4jSEN8ey39qyBA5FRwVAQhEWGYCb+1ElPkFvz0sPzXKfgzDT+Hzfx+LFcLvxjinhsrvhiiThLMiYIJozvHJhpSGg2s8G+UaKfTtNeaE448P63NSaV3pTmFfjk0FzHWe6dOVUSrWt0RpzJjHxXyLei4Qx+azdYVbB0pcxy9W21ptkEQBqRug7JlnoMW1TV1Hi/vHfnyWZ851si7xDAmYCQoTf7OObamLxethO8s0NDy3fKbkhQ/HGLiR5/jX0DkWFedGlM+9J8b7QYP3nT6dNywv87kYAyyeDaMZl/TpnbF4fevI/N7On9krp6PkrWujXAc/8yaQ4J5SXupAY1Xk/czzq6Z1UAa5Vl5513guXC/b3tRso+K/PhY7M1lOszPDPaDjBOoT1lO2+Qzln7zGfvxQg78pJ5QbygD3i87alVGOy2f4m3WZP8lnTx7+Bh0Izpmoz8i/iWOTf9vr/Gafzu/Tt6N8nu3kdcrnR6JcGzgvx/xyjIEDZYR1decmz7OVdYMkyt3lUe4F0xG4dsoNv3Jmril1607he+WrV87Bd7ykTz8RpXxeM2w7KrLd+clhmfzJPaX9ovz+c59eMGxbF8+4bge1RyjI2ZiQiedQMbMPgQHoAX42SkOdyBD8co7KPSu9jSifOz0st6jI6goJnKNu5Aky2syRwUYGSQQ6XCOvDJddI7pYvfHkWOxbT0SlYqf3e6pax/VmxZy4Xj47FSR11bo5bZDEq7l6giuvKHhVwb1JU9cxpb1/tZti+v6wjl/qpW5Yl/gFxh9Vy8jXekzaTYz+tXmC5fq7UYlSWbfPrkXFQ0CVqHS7KN+LY7bfg4b81c26KaejfJZGZD/8S5RfKL4rynXUvwjj2dWvrPhOU6MjLeb90DCvk9bx0CjX+sUoQQiJDs7XhvX0outgCDzfud5xF+VzGcwkvj95pQ4U62d9cZ/eG+WeMXrE+qwTQLklMOL+oi0vr4mxTiL/0umo8y/3vs5X3bBM3UO+e3cs1hdcb10vgcCpPiZlhPPU2vPMWSdIIs+8NcbnkHUI3z/rum7Ylk42y6uibDLHNVE2OT73iDqUv7k3ie9Anrm6WnfY8KOmT1fLWdediZKv+Hu7dQp1IgH4L7UbtLvoNZExqXR4gGTsZaiwHhLlFykU7DqT56RNKstVUZFlBXdLlILUjmitEiTVuEY+M3WN6GK1ygdkSPatA50LYvM8iqngZKeDpBrD4vwSkWPtdJDUHjNx3Pq+dcPy5VHyTzbatZuj7PPCKP+mUibW5QgY2nvCdbHcPrtWff2MIJ6NMtowh8B5o115AOXIHvmMEYpE48bICwEklSb4Tm0gsR8ou3fGej/q4PnOPeMupstpNjxt/qHj0uLesa3Oe5n/Mjjjb9K3ogSl+fqajhf59wuxmH8ZDWP/DHq6YfmqYbmV10vQk8tXjJvvOg/bOU99je155qwTJJFP6tGqMzF9j8EI0BNj+r6ugrJZl8+zsTkQTP/Qp98b/mZ0bZU67CCi3NZvJvgO5MEcTTsX3MvDel8OLSpcKpqTUXoXFBZ+atj29tKjojSGDB8yh4mGtK7g6H1xjFULbLo1xooqU13prxMkUalxjbwumbpGdDFfMbSoMNm3PgbDpfTK6979VHCyG0ESz4be2dko/yYN2/cqSGJdfd+6YZmGnP9O9ZC6KNvOxDi6kOkN42537cMzS6sGSTWCIyrhdYL0g477Ur++yhE27tVBmpuUz+uzUYK2VW0nSALr6VXXy1N5NgP7Nu+RchIso5/sk4lg5Zdj/E6MkE7l3yw77MPn5r4H2M5rOdBgnldt4zhs5zztOerzzFknSGrxvObuMfIVz06gbPIqfArnaJ8nIy+HHSOldYfmXBgk7TFu+Adi81wgMmc9RJoIPOpeQFYgBEYph1PXGQ48GYvXwNwDesp1I0CQ0WaOtpGngeYa+Q5p6hrBurpiYHlZRXRdlF4drw2+G2XuTGsqONnpIOmmWLzuPOe5BEnZoFHR5mdYX1dYKRuc1FXLzM3gbyr12plh/YOa9S32qZ/TdoKkm2Px+niVnN+PPPb6KBXWn9y9x8HGtfN96lc3OQ+NV0X1d1rFbr5uy7ktW70ebbE/I9BTulh8nilHXmjgE8tTjfnZmD5GrZ4XSCck5xjxN/mXjuSy/NtF2X9ZXs268USUeSk1zsO2emRsHecSJHHeOv8wElLXhTsVJOUz4z4kyufUCCgjbdTlG836w4bySx6t5yDxffNHBX8TpS66PErdTjm4bdg2xddte+y1sXkYlQdIRs4KotYWpjoAoSBRUKm4vxObJ6Y9rE9/2KxLNMxtz5/XJl2MhXUqSGKonGvKfXK5jtjba8zPs66uOFmeC5Io3MsqvzQVnGSQVH+eYWXWddW6OW2QRAGpl/Oc9XOcuo4pGSRl5VoHSTzDqWFx1rEtdbF4H6c+x7wL1pE3auQJevCJ42wnSKKR/dsoI370Uuvr4Zy8wsWFUQLwLso8ma1QkfE6tS0He+mC2DxUn78QoyGpv1NWvMvs5sTtfNW+Vb5rUbbbTkzqYvF5JuoL1r+lWsfyVGPOPmyrR31BUHfZ8HfdcCPLBsi/5Oup/JuTybvYXM5bfJ7jnI7pTmhbtlJ9njnrBEmPjjJSRp7K14D52hEEcPWIMMeduq+J1/5z10fZpFNJ2cxnxlykxD3JHwLVnhCls1UHUJTDR8Tyf5WdbU9uVzaYyjEVmCW2PbFdWdnqOshLPEv2o/5glL0Oahi9zLaGvEX+z++adfecfBarPmttAwWOd91E6WRYeor1w75fjMOvn4wS7OTciPxMNhqM9Px7lF/d0NPNgn9i2I/Ji2D/z0eZ0DaFjEHPjVdHYP9LYrGgUsHVkycZYWL+AOd5XZQCT4PBNfLLKo7Be/f2GrM3SEblsyejZM6t/u0J9m0TjRUTUUEgRRDINV4V469YUH+G4fSsgElzPWiOx33keCSOxzpG/vhcFyXYenGMozs0Bj8S89fROhUluMqRt7fHOKeI+/3ePr0kxp4P52Id21imwaXAcu7zouSTK4dlKuHLYvxHPPkurH/jsMznmdzIevIcr8nYzvE4LufkebFMPnp8LP76LvE86X1T8fK8yRMZpJGvee5143g6Nk+4n0Pe4ZqWNXy7iTx8fZRryNE5Ku/PxOKcvdOxubOzl3heG1EaeK71d2K9/88UvW2u/8HthhiDjz+N8jwzH1LOc3SNBod8zn6UhcyLNfaljskGmvqjboT5LPc6fSxKWUvcc/bJkW3qJ/JvWw7IqzT6c40wQcNcB4Z7xnkoI+15trJOkERAxP2jPqGTQnmh7iC/UQdT1mrLgiTuJ9+bQICAoEXZZN4kZfOjMdbhPMuro5TP1tuiPO/Wa6Kci45Q26lOnI996pH7Wh6jnSqRcuSHfeZGRLe6Djqyt0bJkxwr8yTIY/VIO8/g5uG/OB3zryPB/Z5rM7RDsjDXqS6wdQOe6dph2zOjZHgaomxcGbVhn/+KxR4CD5KCmPsTxMzh/BQYjknQxv4cj0Jbo+HlXOxD75pgIK+R78X+XCPLHONrsfkaE5XYm6L0cghc5iq1lBOkpxKBBYWyXlf3Bl4bZTIrlQQ9EO4xFTaVQRaOVns8EutoSG6Kct3MHaOB+Mco95qKtf3csl4JspLj+51otlGRcd0cm/PxdwbUWXHW5yKfZMCWqRv2R50n7ojx11hdLH6G457frMvjt3jm3F/yDvf0IVGCG5aprKica1Ra2SBs5TlRvvOyQHM3ZYX9+iiN5+1RnkPba8/vtF/aZ55pVTyLuUa2i3IsyirPMztGH6/2WVZn1fgM226Lch/r+VzvitJJoG4h7/xdjD/hBvec/Mvnyb90CMm/U+VgLgjCqSidqyxHLc6TndH6PFtZJ0h6XJRjkwhSMlBimQ5la1mQRKDxzijXPBWYUDa515RNzkPZZF+e5Y2xuXxSD9PRIvikzbio2kbdxygXeWDu/r46yvEf0G4Y5DHmAiDyIp1srnnufm51HW+N0mGgjXpRlH86heORt/44Fp89x6o7OARv76iWW9fE9LxPad9kpD/VYwAVND0LHQ68Lmbk6jA8MypyGsutJnzmd7qw3XCI0POmgWh1sV7AdVytEyStK4OkZR0Lgq2pgGEdl0fplBBMZGd5KnBmlG/qFd1e24nrYLS/HjnKEdUc3a9xfwnAlz0Hac/R26T3Mxck8TpyPxpcRpFoPGgctToqIV5TvqrdcAAxurFKgJDf6TBXni+LMgLQ6mK1e3Dc7VaQ9NQYR7YY/b0lypymVvtaezvaEbm511mM+DF6v9924jpuiPJv+yVGi98Tm99sULap83nrIR04ZFBe1TEczbA/c7oIjijIDIdLO4nAl0YnGwt61c9e2ONoYi7MpcPfzPOhp573gFEFXuto2m4FSVshSOD1Utuo7wamFrw/9r8zsB/XcSbG/+ODdCBRCfB+/C+iNFpkWN6Z8+5c2knMWWCuGME4iblRzE86Dhg9IFhq7wFpY9xNjf0KkrBXc/YISh7VrtwHe30dnI/X0SfaDZKk4+XimJ6bpOUYefTV+9H0jNj8f6CQJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEmSJEnad98HfeKhHZm7oY4AAAAASUVORK5CYII=>

[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE4AAAAYCAYAAABUfcv3AAACZklEQVR4Xu2XPWhVQRCFR2LAoEZtQkSDTSDYCf6ANmkURI1FVDQ2BkRs7ARFOxEbSZMgEcTGwiJEUIhCiiBoIaJgsBAbBQ0RKwtBBQV/zmF2fXPH925uLu9CYvaDA9mzN9nZ2d3ZjUgikUgsDdqhd9Bv6Cl0PNO7eLgP/YA+QKdcX9OZgGagZaG9E/oO3YSWx48WODdEFz3O4XFor/77RQW8Fx1kc2ivDx7FnxcDjH/StN8Gb53xms4m6IRpb4e+QXehFcavx0nopTcNQ6KrXyXHoK/QVt9RhxfQOW8atkAD3izKZdHV2uE76tACXZDabrW0Qs+gjb6jybCk8HRsgEZEj21P5osa3dBr0dg826BZqR33wnwRTdgTmf9kz0IfTZuTeWjaVRHLCuO24/HY0msET8l102bsR6VE0kiHaCDTojdTvVVpBAc8A+2CVkJT0JrMF9VgE8cjGzkdvC7jWbgxnkNt0G7oULa7HEzCbfk3mCIwmF/eLMgr0du9iK6G32Hx55j+IusTjf+K8TycJ2MtXYPXBlnOiw58x/l5dIoe0SNQv+urCl5eD6Rx4m4Zz8KkDUL7oHEpcTpWiQ7g6wGLLD0mogi+ZvDIsm6UqhnzhEftk2QvqJi4vcaLMCbGxssgwnly53HxC8E/4hPHc8/i+hPaY/xG8Kbis8PXRAY2KNUnLy7+QeNdDB77LPEVwGeHhbFz4R85P5de6A10T2ov8M+ig8zFYcn/14a74Jo3K+CAaMw8mmOi8+F71DMs+S8GJnC/N/Ngki6JJo5bf66H70KEt/moaJnxuz+RSCQSiUTif+IPGOd5543nv78AAAAASUVORK5CYII=>

[image24]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAZCAYAAABpaJ3KAAACh0lEQVR4Xu2XT4hOURjGH2Eh/xaKTGJWSiylyEJqxMIGpRmSbJSFsqGsWFjZWEtJUrPQbFhIFl+xYWNnbCxookg2Zor8e57e73zfua85957zLSx0fvU0fed9zz33OX/ecweoVCr/kJXUSeon9Zt6TZ2jVlBrqQfDVOyjjrVojFoSknPYSH2BDfycOtoMd7KUOkNt8IEO1G8BNu55agd1kHpMvaJuUvODbGCaegfLl973fwep7SM1GTq0sZP6QO2BzWh4qGa7i83UYdhg6qMJzEUrfRdmbMrFtGqnYc+MjQfmYLFVrv1qv11a7mJ/oaSX0W9tsUfUN2p31N7GJZQbDy/YtjVnsbjxt7C+i3ECFrtPLXOxBuEF4qRgRH9zKDWuI6F8rVwb11Bu/Ags9gS2q5LspSZc22VY57OuPUWJca3wbVi+xmljK9XzjUgb34Vhrco5qg3CVv9EbXexFCXGV1NPYfnalqPgjWvcTbDdodvhRhTL5gXsoZ3FIaLEuLb5G1i+CuMoeOMBFUmZV0wLmI3MqtMV195FiXGdO52/1FHSfXwAtoJ6nrbvITSNpIyL49Qv2FWYtXgXqa/Rb10V/rpIUWJc6LZQfs+1x+hIKEf3vKfNuLgDi3cWZxUc3eW60wO3kNGxT6nxsLN0ZabQpCuntKqLbOP6Utvm2lSA4jOor6zUDig1Lrqq76jGVUNmYdtdX4FJwgt46eHBSKogrYfl6BNTsVOws5maIM9+WD8V1PhDZg11j/qMpvF1sPFCAZMx/Za2YFiY2yZ0gDcc1MPQgF7qAvUMzVUNM+/VucUirlPfYfVFRU//K/ygZqhx6uEg097JjxVLz9FVrAmtVCqVSqXyH/IHDiLCdLlJOTMAAAAASUVORK5CYII=>

[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADYAAAAYCAYAAACx4w6bAAACTklEQVR4Xu2WT8hNQRjGX6EIWShS9MlGVpIkZcnCgg1lYWNnY2VBZKGsWNkpC7LGSkp9yk3KvyLKn5JIYSURCwvx/MxM9/3ec86959xv85Xzq6d75p0zZ+aZeWfmmvX0zJb50kppXqwILImBucIiSyY8U9I1abF0Ufpg1XcwfV1aE+KNrJa+Sn+kh9I+q37U81LaHYMtWS7dttSn57S0Mz+vkl5JH6Wz0n7poPQ7qxUvpGOujCkaY3Jhji2VBtJz6VKu25PruvLTUntvbL30OcSOu+fCA2lFDDZBJ09dmVS4lePbXbywxSY3xqDeWdXYJul7iEVjm6VtITYSOkEeBk0sfhwmNbbLUnbwzWiMPXdT2prLZMidYfW/jJp25VbssNSp56Slzg+HOExqjKwgzeuMwV7phKUTkffuurq3llZsVmCy7LG6Y3cSYwx6Kj83GYMN0rn8C/R/3oZ7nfI6S4dLZx5Z6vhCrMh0NYahZ648yliECSF9C1elb9IX6YjVT3wFZgUzh2x0g67GHlu6fwptjTEe7rOyWhxkl204NoxRHgsb9EeIsYkjXYzRnm9y2RZRpv2nXG7igM28iI/azMOMg+a+K9fCZt0YYsusfvDjjLE6dRNSuGLjV+yGdCbEaOeNYdofMBUw9cvSzc4Nz8qRAvy9wURklLEFlur4F9NEG2MDS/9QPJzUccWeuHIFOmmSn/kyoKiBe4f850S952KFcjdGeTDDfVW3xxnLG2mtDQ+keE3NWVgR0rAJDqLX0nvplKUM6enp6en5P/kLJh+MhDCJnWkAAAAASUVORK5CYII=>

[image26]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAACEklEQVR4Xu2VvUtdQRDFjyRCAiYWKYKg2JiAdURIwC6KKBZ+EETSWaQJFgpKBIsU/gE2BkSwslZQQbTQUmzUTiQBDYEUqQJRSBF1jnM3O2/vru8pFhb3B4d3d3bve7NnZ/YBBfeHOtGjMBjwRPQgDFpqMt0F46Kz7LlVNCt65qevYDK9orEgnmNe9Fs0KBqIqDlb1y36IHoBdaRRtCkayebJD9GaGZ+L/oqG4b/vq+gCFZjxDbowpiNoAqQvmKMzj7M5B+MTZrwLvzHHgeh9EItyLOqCumBt/w49DkcPNDnuukVUbeYcYWL7oldm/FC0gPi7OWZEVWZMF1aQf5mJlbOfR7doxlvw79B5unVrWMA7YRA+MXZbB/JFTTagpUFq4Y+Mm6RTX7LxjeEPryNfO4SJ0Y2n2fiN6Bf0WC18d040ZGJMts2MublUOURhZ7LzYryFuuDg8bOm6NJ1cLOf4MuF3f1HtAdtjrK8hrY2m6BSXIemYPOwsx0s/lP4hnhunpNMI32/1IuWsk9LucS2UXqRMpET+M3TxdQJ/ecn9EdshzomoXPvgjhj7MQY7aKmIEZ3bGLEXi9RaHFq953QG9vCwk3VGJ2NXQ2Mh46N+uk4rK9UYoSFzzXLokPo2pclKzxMivdWjH9Ql5gUr6bYDVBCv2gqDAYwkc/QLwz/ahwN0GNM8RF6OqsobYyCgoKCm3IJD8BmEt06NCEAAAAASUVORK5CYII=>

[image27]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAZCAYAAADe1WXtAAABRUlEQVR4Xu2SvytGURjHv5JBTDZSryzyD8hoFxkVZosselPyD8jEomRgUEpmheFOksViUBYmpWSyKD++T895zn3uOd13M6j7qU9v53m+97nvPecADX/FKr2ki3QwuElvfIh002n6Q7/oCu2rJBzr0GDqmg+RPfpIB+gQNHNPWz5kyNA7Ok/n6EilW2IvM4qwfnO1iAwtaH9ST6kb+uJqET90ik74Zgdsb2fThmCffwgd/kC3aG8ZqdBFJ1EelqwzlugO7XG1J1Q/1SO3Yxza30WHG5ByBX2o7t8Kt9DMedqo4wj6wHDacGwgP7yINRZc7TjURsO6FdZnMQHMhJqY3RwpfkA33yhC3cI24NkCZDnUxOywLugByv2TXwnux4QeotyKMVd7R56LyL5dQ0Oyl690G/khndBv6JBT+knbqN6ahoZ/wS8KAVJWsdzycgAAAABJRU5ErkJggg==>

[image28]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAZCAYAAADe1WXtAAAA8klEQVR4Xu2SMQrCQBBFR9BCLBQsRBA8goXgAay10doDKNaWdt7AC4hlPIkWYuEZLK0sRFD/sNkwmWziFiIIefBgMzP5JOwQ5fyCPjzqYkgJTuArdAbLsQlBHfbIDPHwLd6OCOAeduCSzOwBtuSQi7TQBrzCqaitycw/Rc1JWmiXTO8iasOwxmaSFsoMYFM8j+gLoRr7+3fd0PiG8ibwLF9eVfUS+IQW4AJuYUX1nPiEjuGDzNd68SmU93lO5mstK3F2khXahieKBxbhTjxH1MisCr/EobzMfJbrw5dh10crdzdiQ8lBq8Uuv8uzmMvJ+QveQ9JH1qbQ188AAAAASUVORK5CYII=>

[image29]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAWCAYAAAC7ZX7KAAAB/0lEQVR4Xu2Vv0uWURzFj4hgqCgVgSC4RBItgdSkEmLgooMFBf0Bbg0FRk4tDTqEgy4RiJODLiIu4eBsgYuCmxouEtHUYvTjHL732/t9r++rvPSgDu8HDjz33Ofe5zz3J1CnTp3zpCM3GqhBaiuvqIEr1D71h1qiespqS6xRv6gjai6rq0Q3teCFDVjjFdiHfnhFjcxQv0P5GrVJ3QxeP/UllNupdeordSf4kVFYvn+BnRH8X+BD2OhGJqk3ofwB9nEFdYZh350NXkQzrkyFB1ZbTXVEfX6jbqeyZkHvPfAXSFvyDoLnaHRvwMIWGrgV1jbvtA+2TIZSWWv8IWy/OF2wtloaEfm+nwoP3InKgXuTP5b5jn5gldqGjWREYRVanHvgV5nvPIHNwN3MV3gtB6fwwNWWxL3kq++cbuoTSqPo6CT5nHmFB26GtV3OfPX5E7aWI36cXU3lJuo61ZL8Y9jx51JZKuOswOpUwaqhqd3JvBewkyO2Uz863rR+nWc4+bOOZm8DNY6wGn1E5c3h6JL4Hso6Ceapp8FrpF5TU9TjVDdN7VFvw3uRE4F1R2vTvIMF1khpfclz9HyQ6qvt+EewS0EjKO7DfiBeEhOwPipJo5yjmRmgdmGDVTO6uTTNpzFOvaduofy8vRAWUboELj2a6pe5eZl5jvL1WOcs/gLeBYM9L9lSJgAAAABJRU5ErkJggg==>

[image30]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAWCAYAAABpNXSSAAAA0ElEQVR4XmNgGAWjYBQMW+ANxOeBWBWIJYFYHohjgDgPWdFgB0FA/B8JfwPiUhQVQwD4AvFpIA6BYlZU6aEBQJ44gC441ADMExxAbAbEwiiyQwSAPAHKC3xQvhUQvwdiE7iKIQBcgHgtEp8RiOcD8S4g5kESH3IAFjvl6BJIQB+IH5GAmSHaaAPWQzEyIMYTgwrA6gdkAHL8PwZIUhsS4A4Q6yLxQfUEKGaGVJ6YxYCasROA+C8QGyCJDQkAKpEaGSAe0mSgcSYcBaNgFNAOAAAksSlcGwILLwAAAABJRU5ErkJggg==>

[image31]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAWCAYAAAC7ZX7KAAACR0lEQVR4Xu2VMWsWQRCGR1RQFEUFRbAJihKLNEFtDFjYBNEiBuIvUCsLBYVUadKnC6QRCUEwaQUJASHpgmCjCEIgBmMjKoiCKGrmyezmm5vv7nIRixTfAy/cvbM3N7c7uyfSoUOH/8Fu1c5obsZJ1U/VX9U31dliuDF7VctieaZVZwrRdih2QnU8BsRqeCqWa1V1IAeWVNfzjVgSBv12XhPGVH/c/RHVouqU8yJvxN4VC+YZXxO8zRc88NwF4EvymbGmvBebXc+waiR4mV2qT1Je8N0SbzRf8ADyTCWvN/h1MJ4l9FwVK6o7+CdUL8XiZQXzocx+j/Oe5YuLSZ4FsUTHgl/FfrHxj4JPXtrkcvDHk6oKvpT8vMo7VD/8AA9BBn6MgRp4YVnBrBD+gPOOqq6l66qC4b7YPsqFb2y6yAXVd9WVGKhhs4IfpHsmg81J/0JdweTKewnRIgUOquZUKzHQgKqWOJd8CoN5Ke7+soI5pZ5I8XSh5xlXgPPwlbQGcpjzcBP2iCWcCT4F/ZLWHmHMB7FJQZ+DB6wKK8xqeKhvHQL0y+FWbB1ecsjdUzyFVcHmeh08jidOjqrnaJU4w/3Ji2yMGVJ9Vd1QDSbxNS+k1Wss+azYCrBpyuAnQc9lmIiHYnmrKCu4S+xMp0U9ffnC78SoDAnfJc/veA+9Sa7cRufFPiC+GGg3PpyeJ+dNsT7N3FZNqvY5jz/yluFAZ5nruCW2QqelvQ+3AsWyB8hFzn/isbT/BLYtLPW9aG5n7kh5P3aoYg2bKoa+hmi1VQAAAABJRU5ErkJggg==>

[image32]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAWCAYAAAC7ZX7KAAACXUlEQVR4Xu2WTciNURDHR1KUz16RIiWRhSxEKXYUCxsSdsqClYW3KAuxtJGFLKRkIQs2kgWrdym2rGwQKYUoC+Tj/3vmzL3nOe+578dT6qb7r3/3mTlz5syZM2fONRthhP8Xy8V5pXJYMUf8Km4tB2aABeIr8Y94V9zYGu3jjPhO/CxeKsZyLDa3w9+VYqzBQvGx+M1mHzAOf2fymPhUXJ/pVojPxT2Zbpf4wHyzOdjMk0wm6EkYF79Yt4Dfmmc3xznxQibzzcKUXGCR+UZ3ZzoSh25vppsU8CPxpHmgXQLG4cNCt1/8KG5K8mtzOwLKgW4ifc8393PbvDwHgoBx1CVg5rHorUK/09rZmypgxsBq89PidKjh6+I1cW4ab2rnfgjWLeBVVg8YH+gPJPlOkimDwLKkY03AqSD/EA+HUdI1oAzIbuBfBHw2yVyw7+K6noXZDqsH/Mx8MwE6V9NraTF5rXQJeFBJbEt6gghwtGTvk3l9H0o2L9I45UMZxSYDTcnsEz+IbzIi44Dfy2E9DbgozLlX6An0p3kt5yBRK83nlXO3mGezGnANLFLLMIvgfBDISmQpcNr8xsc8usV7cXvPwtd5Ka5JMqd9VbzRs3BwEauoBRwPCk2f5l8DjwTNPsDCN8UjmS7qM7KHDQ8O9ygHD8uEtbsJJ9XCmLhWvGju9Ly4NI1xqaIlxY0vcVD8Zf3/IGSRDSzpWfTvx+YkH7P2nAAyJ3Y0k7GbNeiNHPNUOGHeOzdYvfGjIynYRBnUgB0+sDtejM0Y9NH8CR1qcCzjpXKYccra9TjCdPgLnzCOPsB39mgAAAAASUVORK5CYII=>

[image33]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAWCAYAAAC/kK73AAACB0lEQVR4Xu2VPUscURSGjxghoiBoiAiCQoQgiBgM/gIJgh9IDKTQQoikstJCbUKaNBYWNopWaZUUqSwMYbHRwiKxUUJSKIJICGliwMKP991zr3vm7s66q2shzAMPO3vmcu87c8/MiCQkJNwbGuFEWMxDOeyFm/ACHovOYWmAW7DLHdNuuAirzLii+Si66DL8C6eip/OyC5vM/xrRuTiPhxdy6OreFVcvCbwT+1J48EfwH/wAK0z9XDTcA/ef8+7AV84Xrl4yig1eJ5n2eGrqKVfnfIS/367O5ueTaAvFwV16FxaLDU4GYUtQ823BHSE+OJ+HJ7DPHeeiFn6V3L3Plvwu0d1Nc5PgIZWioX+Ymp+33dQYjuPKTM2y5uQzQ3hzZiTmgksRfAT+hs9N7bFoCMuAaPBnQd3DwKuiF9gKf0r8Rd46OANvhMUY/FopWB09FaEH/oLNQT3CbYKz/3iH/NZyS/228mHadseeQoLzXX8E50R7O5brgjNIuAiDrsP3Qf2lZMb+l+jrkXTCEzhvapY/onN4uDbbhW2TRb7gXHRB9MNi+/ILPIDTou/oYbgE98wYvsPHzH8yKrl7nH38WvRrHDIp0Yc+fWcY+i08hZ9hm6v57a4X7TUu1u9qfC3Zr2GoZ0iCBUXnOpPsB46h2R654Nhx2BGeuGveiO7GLHwYnEtISDBcAuKmbM9i/NsjAAAAAElFTkSuQmCC>

[image34]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAWCAYAAADafVyIAAABQUlEQVR4Xu2TvyuFYRTHj6Qo3Ugp050MhptBGQwmg5JFMhlsN3/A7dbd7j/gD7DILFlkYXiTzaBMBguLwaCExc/PcZ6j8+KKXovcb32G9/uc0/f5cV6Rtv6NZuAIhmEIyrAIu7GoiObgOXAHNeiJRUU0C4cwn+jKLxeXBmTvzd+UB3TDOAzkVk17cA47UIJtuIEDmIQOWIDj5G9Ym0kD9O61UTUBV3D5VmHSt3qS/OOvifU+iIWo+sWuvOpFU7DpH2KF3tgbfN2IBkwHry5WdxE87cnSWkv5qWKRercwFjwPyIL3IWArEdUq4EzsX3F9FdBww+c/yhv1+lw/DVh34xQq/iH2H+iJPnuDaxgN3rcCViX/yEvwKDaWrjKswD0si410n1ifBujJBsU2p2N7AvuvnUk6OU2xsBHojItt/V29AOWhTwPngVvsAAAAAElFTkSuQmCC>

[image35]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAWCAYAAAArdgcFAAABB0lEQVR4Xu2TMQtBURiGP2EwicVoIIMyGSz+gZFi9xOU+Ct2/0IZrBalLCzKZFBiUeJ9O+dwfPfexChPPem+3z3fd9xzr8ifn6UAL/AGT7D8Wv6eDWx610kxQ65e9jVsNFXZweYplX8Mm1Cfsc2qKu/CvMp8FmLueVC3+szENM+pPC6mQdgAZn0Y0wUfFtl4rwsWDhjKcwB/V2Iav6UGz7ChCx48dDZ0jTmMQyNJwwnc6kIEFbiDJV0IYwSXsGivuRPuMIo1HIjZuVsTgM+Yzyurch5yRmWEjdjQHZxbzyxAGx5hB7as/BdzmPDuc4QdnhsQeIv4Jbp3Xavh4p6Ev27M3CH/+TXuAGYzQmZDGsoAAAAASUVORK5CYII=>

[image36]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAWCAYAAAAinad/AAAAr0lEQVR4XmNgGAW0BFlAPAuI1wGxLpocTiADxEXogkDwDIj/A/FXIDZGk0MBCxkgCmcD8XsgLkeVhgOQIQQNgwFJIH7IMNQNAwXJFyC+BMRhyIpggBjDQGF7C0kMpBYkxoMkBgbEGpaDJOYLFQPpRQHEGgYyAAYoMgw9AgaPYSCNnkhiGIaBYgLESQPin0C8EYh1gFgMiJmhakDyoPwJ0lgF1QPCfVCxCKi6UTBQAAAEkTaAHNOV/AAAAABJRU5ErkJggg==>

[image37]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAWCAYAAABOm/V6AAACNklEQVR4Xu2VT4iOURTGHwtFlESkSGmiiZ1/WahJlmwYpdhZKNkpykpZsZKspGRhI5uJjT+LrywoxYbYqCGRKTMpFBLPc8+585175v1iMWVhfvX03XPOfd977nnPvR8wx3/AC2qSukotSrHKNupZds4WK6ib1ELqCvWUmtfMMHuCOpH85aGX1C/qO7W6DU9zjvpAfaYuUavaMI5Tu328ifoIS+QYNeq/su9Si31e4RZs8cg7tOVSkpq3PfiGYPOWub2SeoV2A9fCWGjhO8lXUALKOHLd/ZUd1De02ausmnfQbVXltf9WchL6BDOS0Eu1mB6OnHJ/fWHP7YzmPaeWw5JSM271mCrz0MdiCTr6QPwpic1uK96VxCFYFYfd3kmdhSV0mBpzv+yTSH0Q0cvfJp86XP69bn9xO6P4V/R3LzZQ59HvDVXgHtoqjFBbgl2a60d0wJL62yTivC5UAfVBrcIu6gHslCjBgkq1B3bs3lBT1GnYy2uZB32OfbAE62fL5D44g3bDj8K4oItGjaiML8IWXeoxNV9XEuqd99S6HEB3H6gCSrqiY194Qv0MATGOdrIuISWxIPiEbkUl3EUPM0+DKhr7b/oId31v2ReCXS8mHbuKdtiD3SEZVUG71CUXeYx2czoAhXHqU99frt37CE2DfmkljcV+WAXn10kB3awbsxN21Q/siTXUZdgi62MgoYpojsqsZ7pQn9zITkcbOEDddq1tw7OHjuCgP8DKUepIds7xz/kNR2l9rzgHGCsAAAAASUVORK5CYII=>

[image38]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAWCAYAAAASEbZeAAAAoUlEQVR4XmNgGOIgD4h3A7E8EEtCcQ0Qn0BWVA7E/9GwExAzois6D8QhQBwAxArIkjAAUnQAXRAdwBTxALEDEJshS8IAzE2cUD7ILSD+LLgKIIgF4onIAkDwgAGiEC9YyABRJAMT2A/E0+DSEABTZAwTAHG+wqUh4ABUHOQZMLgCxMowDhS8YkBz0y4gnoPEB/kSw3cgwAzEXVCJdDS5QQcAdcoiXrjD1c4AAAAASUVORK5CYII=>

[image39]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAWCAYAAAASEbZeAAAAPUlEQVR4XmNgGCaAEYidgPg8ugQIHADiv0C8EYj/A/FXFFk04MswqoiBUkUCQCwJxH0MEEX/gFgeKjZ0AQBH0hyqEmkoUQAAAABJRU5ErkJggg==>

[image40]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAWCAYAAAASEbZeAAAArElEQVR4XmNgGAaAE4gfAPF/IP4FxOooskAwAYj/oYmdAuJnyAJPGCCmIIMqBoipcADibEUWAAJfqLgmiMMD5SxEVgEENkD8G4hdQBxJBuyKjIH4KxAHgTiEFJWDOLisMwXibwwQtzFwMEAUrUFWwYBwOMhtYAAKo6twaQgoYoAoAhkCBqCAew+XhoD5DGjhFAzEf4GYFUkMpGkPEh8O0oF4FhA3AjEjmtygAgCr3SfloRfgdgAAAABJRU5ErkJggg==>

[image41]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAAAWCAYAAACrBTAWAAACbUlEQVR4Xu2YwUtVURDGJyoo0lpIhKBIEkSrECUIUheSCIJQVItq16JNqwSlP8BFraJFgQiuRHDjxkIk6O0MW6RQBFGLopYRiAURld/nzHl37uE+xTbFvecHH/fNnHN53DlzZs69IolEIvHP2A/dhT5D69Ce/HCOV9DJ2JnYmTHou/0+Az2EWrLhLfZCF6DRyF96+ODL0B+79uWH61wRzUDO45X3eT5Bj539G/oB3YAumd6J3t/k5pWeSdGHDlubW34OGqnPUJh5dySbxyvv8xlJe9zZK9ApZ5M16HrkKz3MNspzEXoOHTH7uGiWxgH7Br1xdhzkVajb2fugadGFrAzcsgwMg+VhYOi/afYDs5vrM5T35g9wsWac/UyystAhmsWVY6cgT5nNOltUR2vmDyVkSTTwhLsglAVmLjP4kdmVoyjI18z/FDokWTAbBdn7D4rW+avOx8D3OvsA1CMVKhusqX7L88Hnzfc3QY7hmG+Yw9AG9FK0MVaGfuiXaHObhQZEgzdh4zWz42AGPxeiCJ6V3zqbjY+7JjTDY+53Eaehj7tQfKT87+BLQ6toxp0TDV44xrGZFQX5hfkbUZP8EY9B/SD6P4T/FZprqXki+ebF6zR03/kY9J9Qp9mBL6IvG0Wch05EPmatDzLxR77S8lXyWdplvo76DB2rQUPOR3hkW4x8pE2Kj2v0x5l8OxsuL68l+95AWAIY5BhmJhtheEHhlfNYd2N4uqBiePLghyPWWsLycTYbLjesxwzKPdm+ebDBXRZ9ORmMxgLtogvSiFuizW9B8k0xsQuOyvafOAkXgh+NDscDiUQiUVE2Ad2kistL7LeTAAAAAElFTkSuQmCC>

[image42]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEwAAAAWCAYAAABqgnq6AAADyUlEQVR4Xu2YS6hURxCGK0TBoKLiC1/cewMhSAQJgiKKD/C1UVxoCAhmEcQsBBeCBlcXxK0LEQURLiIhIu5EERPIgKKiCx8oQhIhiuAqZBMXJviob7prpk7dPjMjN4QQ54OfOadOz+k6/+nu6hmRPn369PnHWJL1LpxRfRiD/xfGq2bFoPKpakT1l+qN6obqg0qLMlNUW/LxGtU2p605Xge50K4Frj+QlACfX/iLXfhI9Zuk715TrapcrUI/91Sz44UCJ1UvYlCSUbdU36p2qY6qTkh6qE6slHa/Z1VPJeVs6sQmcW325RN7S3weyvFukOhrd07S56T9JoFp86fqsuqS6olqjrteYlBSTt4w8mJkfZzP/ZRsqC7m4xLzVPdjULmr2qt6qfoyXDMWSrp/y7Bnqt/tJEMij6T7SKCjhyGGWZjDyIsckO6GmenRsGmq26rJ+dwMI0faxjw8mHE9BiUZxsgj37qc96iGxRnGwVU7yVgSh0PcM0FSm+9CfHGO7whx6MWwn1XLZLRh9McoOiXpwfwIW62amI9L8PIZKREM4x5DkvobrlxNXJDUX9Mwe+iGawCTchwz6hbUGZLanA5xzCB+MMShm2H0u19Sn9Ew+CbHuQdrV69V8nvVuBiUtmHWH8Z6iNtUbRpmxjRy0PBxjkuYMXWGxTh0MuxzSaPLKBkGNl291lVaVGHBrltazDC4Kele3tjd0h4w/znDfpBqoakzDBZIGsEUHNo9llQoIjzssRh0eMNYq7jXonzONDyfj6Enw36U+rWhzhiLs9ZE6gxbqvosxEqG8b2BfOzXMMs1wnT6KQYd3jDMHZFUPFhuMBoTjaZhNncb7gJQkUpmeKhWpTaUfeKYE6kzjHuwL/LiHojjI5I2nkwb9nHTpWoYlZ5RFqHy+YeOeMOA6cuo5ZPvDrlrTcPgb9VzdwGoKGwZlrsY5k5158BNKPUe1hMewHdm1BlWIo4wq5L2XW8Y+ZemXt1ib5DL5hCjX549rostwxpS3XyCOez3Jawvr6S6Kf1F9Yc7B94oyWNwZCyGAVVyZj42w9i3xZcLzBKfawlebDSM56FvRrSnZdh6SUZYAz5ZD1hXDNYxYnGqWZm3nyUDkiodnwY/hzCI/dkVSSbszLFSQaGifSLpvoz++dIe2eR2R7VCkkEbVcclvcz4gjpVR6Y0I4g+flV9Je1nYFS2zJGUp+VTYbukzjdI999lka8l/fZjw/lv/BtAHzzwWhltFLAcxD3Ve89gVgl+ZbCk9OkRpm2p6PSpoVt17OOYK+ViMmbeAkoX9wk7lG6bAAAAAElFTkSuQmCC>

[image43]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE0AAAAYCAYAAAC/SnD0AAACmElEQVR4Xu2XTahNURiGP0kRMmBAqesqAxOUAUoyQAyY+BswUAYMxEARM1NDEyUTA8Wd32J2igmKCRmgECmSiIHk533Ot1fnO+vu83PlnnPSeupt7/2tddbPu/da6ztmhUKh8H+yTPok/ZbuSXvbi5uclg5LY+b1V0kPpZ2x0gCZJ92W5ucFFQekx+Zz4jq7vbgJbbw0r3NX2iLNihU68UQ6E54x7Kd0RZoT4ufNG096b/UDmUl2m/d9Q3ogNaQFsUIFL/ictQzgyu+IJy5Lv8Izc50wn3tPaOxReMb9W9J3aVOInzUf9D5ptQ3esJxrVm/auPTGfIyRb9LT8Mz8+GAie8z9wIOupC8nkt4oRiXi/SjQybRL5mNfmMVfVHGYW91fbxU3WSt9kQ5l8SlslrZnsbQUj4VYMo1Bbq2uw6TONMyYNB97Pr5GFWepLqnuaSPCXv3KfP7TAgNZ1+xzcVPEtAvmny7xg+Yb7FioM0jqTOOeWDfTiGNON9PyeE/umzcYDwE4nsXonHpsqMNgJEzDEAw4Yn0eu+Ydp32iE6/7FHvOdNKXvzWNFKWXaVezeEdYjl/DM52mjtdId6RFreIm/Zg2U9SZxstmc68zjRQljZVDos60ldI76/PQIzfLj2hM4hSFNJCNreImxD5msUFRZxpwsP0wNyDCOEkzEowdIyPbzHO38Sw+BQyjMY5ZcjC+OBLbD9L6qs4J870usti841Ha0yAt0XypYwb5Z+KZ+b+gCPNkTj23p7TEcjWsfUDLzTu5Kb2t6iwN5YOAl0iSmo8VpVUBTJp67E8nq+uuUA4k56fME/uj0mfpubQuVvoXbJAumudvK9qLRg42/P3mye6OrCyCYaws5jbsfzmFQqFQKBQK8AcjjbLpsRG4oAAAAABJRU5ErkJggg==>

[image44]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAZCAYAAADTyxWqAAABAElEQVR4XmNgGJGAA4glkTAzqjQYiDFA1BEEk4D4PxLOQZUGg08MqGr2ADE3igo0cBuITwDxPyD2QJMDAR4gLkcXxAW2AnEAA8Tm5UDMgirNoATENmhiWIEIELtA2TCvNMBlIaCKAdMCrABkozSUDfIuyLDrCGlw4INcThCAbFuDxNcB4vcMEAM5oWIgV5+Hq8ADQF48hcQHGQ4KM5BhllAxkBeRLcQJ0hkwFfIzQGL2CRArAvEdBiIDH2QQtigHpTdYRIC8CPIBQXCVARH4yICRARGzINcTBKAABoUHLgALO7yuAuW/UCDeBcSPgDgeKoYOQDkBlCNArhwFo2B4AABPEi+t02CmNwAAAABJRU5ErkJggg==>

[image45]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADYAAAAYCAYAAACx4w6bAAACl0lEQVR4Xu2WQahNURSGf6GIUhQJkZSMJCEDMyYGEooyUQYkI4qIepIBo2fyXklJhhhJKcpNilJKEb2XuhQyQMTAQPy/dU53nXX3fvfc+8rE+erv3rX3OXvvtdZeex+goWGyTKXmU1NiR2BWbEgxu1C/aPJB3suxlLpBzaQuUW9hjnrk9E1qcWhPcpn6Su2hdiW0qvNohZ3U8diYQYt9Rf2m2tSZSq8xRG0u/i+gXlLvqPOwdeylfhWqxWvYhCmNwSIZuQLrr+PYKHXP2RpP4/qxl1MfqIXlQ0iP/ZiaFxtztKmtsEH9S5uo9c72fKR+Ij155BPseV83h2GBGSrs1dQ3TOzYGmpDaJuQi6hOqm1zC7bPI2XfIuoNuidPIafkhA+aHFBbq7BnULepdYWt2r1f/BfHqLvOHggNkkv5UdgEWlhdx1ZQ20ObHJBjcqZkG3UCFmTV7wPXp3JRxgZGkboDy0xEfXJaE/fjWEQn23NY3c0JfSupC8Wv0FzD1HRnL4MdLn2hk/FAbIQNKKfK430yjp2FZSt1KEWUxRfOvg47wVW3qtNe991fNsIOBF/AJdp+B509qGM7qGuod8EqS6rzMltan07j0hk5Jrsn52CRTF26an8PuzQl/Vfb98LW9uqFTtjP6CxUv3M73V3sRvUiPoJqIFWnj5ydRfeIFlsnvWupH0hnTE7G4Gjb7UN17JPUVWd7dPJqy3r0rJ9PTvsDJosWKsfqkHNsGmyML65NTukyPgT7gthPjcACGd8vaaH7YFEgYsaeOjuL6quXY8pEC9WvE6msS2VEnzwPC1vEZ0spMAqQR86onlO7RnOPU0tgwXpGbak8kUF3x+nY+I9RRrQNczyBfXO2qVOwHdLQ0NDQ8H/yB6CsjcO4lVZfAAAAAElFTkSuQmCC>

[image46]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAACOklEQVR4Xu2VPWhVQRCFTzBCxAQLiyAo+SEg1vGn0U5FsYpoCrFLYSMWBhRrO0sJEVQQBCstFUQEb50UKggBNUVAEAQJggYS0eSczC53dt++Gy0Ei/vB4b6Znbd3Znd2L9Dy/7CH6sudGQPUttz5r7hGrYTfh6lZanc9vImSmaCmM39X9lL3qHVqmdqRDm8ySb2DxeiZV/yJeubs39QqNUWdC/oI+3+/iyvSA6v0LrWd6qUewl6iZCOq8AYsXuipF/jKZV939hx1wNniLXUx8xU5BqtqMNg7qZfUZ2o0+EZgieYv+UEtODtP7A017mwV/QC2AFuipDRhE7dhMWpYz2LwR7R1j5z9CvWWDcFW64/RxKp8P3ULlsSRJML6ptQXVfDH7X0BS1bsQr1lWiGt1J1gb4lepIml4eDTS2aom+G3qNCcmPfr0KhfLzifklXLRHSVHETDlvrEPMdhqxj7o0JnAk1+j8b8oTlDfadeww5HETVj3EqPEpL/CSymCnaeQPTrwJTQXfbe2ZrLF6wD5w9HQlNiFSwZNXQpsfng70aF9DpRIkuwL4PQKl6qh1O+wk6TJyZ2OdhHqZ+or4+I/qtTXeIENZb5NK9PTPjrJeE+Oqs+S32g9gVbK1VRp2JAQAU9z3xCF3PpapA/X7Gr9XAnh6g16jH1hfqGulkjsrXlmvhKeJ5OImqU1FDuDPyCrZLm0xen9OlLOAm7w86jezPLr3HFKb6EVlnb2A21hwp8ivRgtLS0tPwtG9k9fMUx5GZWAAAAAElFTkSuQmCC>

[image47]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAABs0lEQVR4Xu2VzysHQRjGX6EoohykyMXFwYncHJ2UEie5Obg4UeS/cKI4yMF/wMXFnl1wFQdyoaSEovx4HjPfZvb97s7s1jc57Kee2vfd2Z1n35l3VqTi/9AHtemkohNq1slG0a3iNejNXo9DW1CPu/0LzcxAqyofpB9a0ckcOPG+yt1BR178Bb1Di9Cc1RX0DXV44zLhyzlwF3qC1tO3M9kQ84w2xpz//Ck07MXkAlpQuSDcFzdSzNg99ChxY+fQqBe3QHtQq5eLUsRYE7QpZt8kUm+MS3fgxSfilmxQTLVKU8TYtJiXc7JE6o0dQ9f2ukvckrFCrNS2jUsRM8Zl2BEzSZ4x0i5m3LyXo9kJL+ZRMiYFlzRmbFZM15KQMQ3Hslm4DcgU9AKdiWmOKCFjrAD3Vo2ixnikXHoxq/4qriF6vetcQsaeoQfo1orn1Sf0YeMRNzRFIumDlEY4B+cirOKSu51NyJimNjZUsUloSOVYHd8Yic7XSGPci1lHA/O6Yrl/Ghrhwailv6wGzeixep/QFM+tLLgFOCdN8d/KLv4TBsQsYx7LYhrgUNKNUVFRUVGWH+AEZGdnpid9AAAAAElFTkSuQmCC>

[image48]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGUAAAAYCAYAAADjwDPQAAAEW0lEQVR4Xu2YXahVVRDHRzRIsBSCQizuJRCxHiLMQiyUi0JhCH1A9gH2pg/6omQgPijiQ4UgvgiRyCV6KFQKFUofuvhgIVEIxo1QSBFFA0PRwCJtfsyeu+fM2ed4Dtdzrhf2D/6w19prnz1rzZpZs49ITU3NxDJD9WDuTDykmpo7JyGPqh7JnYkHckevmCK2+JFNqr9VQ6rnVVel2WAc8ZpqY+qfbAyofldNF1v086rlDSOMA6rR3NkJD6v+UN1R/ah6R+xl7XhD9WHqu6A6ImWUrFPdUn2nerPQGbH3ZIf2i9mqnWI2sGm+leqIfVx1Q2zcPtW8xtuyVXU7tFn4f1Ufic3zXdWXqv9UK8O4jjgk5mV2PiwSW0iMmeaDEhjJ/eyU3McCzA9tOKV6L/X1C1LNT6rFoW+VNNv9q+r90CYSPlU9XbSfVF1SnRsbYc/vDm1YK82ZoiP4YYzyxWMhvY/rKi6LOa4TpywIbZyMQ/uWYxPYgo0seu4bCX1XVHNDGxaqNhTXz6iuS7NThkP7WdXZ0O6KAdXq0OblnAsYmg9rUhqRNUfMoOwUwvkLKaOOsPU0xXuIkomGtBI32+ticyWlObT/lHIeQHQvLa5ZF9I06+R8L2Wa4rljqpnl7fGxXcyov/INscOZl3k0ZaccFdsdg2IGMdYhQvaE9v0AEfuV2IHNpnE8fR8UO1vIIswrRjgO4Lxwxx2XMlW9IBYp48YPtRNihmTY8VRXGNHKKUA0USjEYoFc/NLYCNtpz8nEpTFyPXNFn6d7wBz9rEGku6caRpR8XMjZJeZoZ1D1Smh3BYcgi/2L6h/VB+EeRuIQT0XtnJLhGSLId9QKsQ3Ae076oD7DZmAOL4sVOW9JY6piM30i5gx3TIyKdvDMYHFNtrim+lqsEu3k+Up4kHMBQ9gtQBpidzndOIXUwDcLcNDflPLwfyxcV7FebNE6EemFRe4WPmKZKykL3EZSkIODGDMqZnMVXqF59HsV647AKaTwjphVKMJiY8R+MSO5vijlAnBNHzueNlFWBTslfiQyIZzpBy0Grylv9xzeV/V95NEAnB8+7wjfZXyHvJj6HaItFjJUav6bQAH1Q2i3BAOjQQ71Nn2fpX6H3c1uahcpfN3mkpDnolOg3W/cSzy6mVd8J+dbXAMWfUd5uwHKYMrhDOmOAimmp2FpXFfOaYqBu8KPZKfwAr5y6av62wA6cQq7ht0TwbAcKV779xo24IjYebks9BO9zJUS2NunpTn6eZ7Pgap/OsgGufzdLM2R8nNot2WJ2F8fHEbkRH6Iw+ntOKjAJ+aOdMWdD4T6QOpzODBxJg6heKiaZK/gncyNcp+5Umxg/1Bxz3m1GPdNMQ5Hcp5UwXnLPDJe4DxRtNmkrTZ5Jfz3s03MAHZR/mjsBoxgp7WCA48oOyxWBPQbDmKcwFyZM6V5FawBpS7jyAxV/49Bq+gBMsNvqr2qLdJ8TtXU1NTU1NTU1NTUNPI/Dhr3vDw9ZpAAAAAASUVORK5CYII=>

[image49]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAAB2ElEQVR4Xu2VzytEURTHv0JRZGEhRbOxsSalWFrJQqywUBY2VhTxh1AsZOE/oCRlyooNFrMRC2VnYYOy8ON8577rnXfmvpk3iizep7717nlv7v3ec889A+T8H7pFLTZoaBc12uBvsSp6jZ6HRJuizvh1GZqZFK2YeBDu8En0KToXTSVfV3AiWrZB4UF0qMYfojfRgmg60i3cOm3quyAluJ16aOpdtC1qVvE9uEl34CZeU+88Nn4h6ldjci2aM7EgnOxSjVtFR3A7HVZxD7NrDXhs/Eo0oMZNol0kN5wKJ6M0E1EstHg1Yzy6fTU+RXxkBbhsZWZENGZiG3CLL5o4qWbsWHQXPXcgPjJmiJnaisY/giZZY6y7BvOOVDNGWAqszxkVo9lRNWYrGUTGI/WwYLlw2o9qGbPwKNcRb3Jc9AxX11yrJjTCVM8jnClPPcbYy27UmMX/gvhCdKnnVHh03ImHOw31mnqMFZFspDRyDzcHYQJCdfwNe5ftN2dwt9OS1Rhrtc/EmB1tjKTOQ1PsWbNwnZmZY/E+IpzmLMZ6EG4NjNuMhf5Byvg+ZlVE8ihpxH5DcSELTRVsMII3nnPRFJPAW/wn9KKyL2qW4C7AAZIXIycnJ6devgAnQ2iPLwkxvAAAAABJRU5ErkJggg==>

[image50]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGUAAAAYCAYAAADjwDPQAAAEGklEQVR4Xu2YXahUVRTHV6igWBgIhWLcQQSxHjL6EMEelIKiDxIFwcQHfdAHfdEyiBDFhygQRKJCi7iIDyVColJp4PgBhoKpJEoUXKPyQTCUElLU1q91lrPOnjPnztzrveOF84M/M3ufM3P23utr7yNSUVHRXR5UjU07Ex5SjUo7RyCPqCamnQlj0o7hZJ3qumqe6jnVFWkeMIaYr1qb9I80elQ/q8aJLfpvqhdzdxi7VefTzk6YolqTdgZWq/pUt1THpNnTf1ftl0aUrFL9q/pOtTDTL6o7YtHUDaarvhAbww3Vt6oHcneI7FF9qpqUCQf7QPVouGeD6nZos/A3xe5jnm+qvhRbq9fDfW3RKzbA7aq/VO/kL//PaNUnYl4RYRArQ5v/ib9nQjNCG86oliR9w8VTqgWhjTGIbsbNp3M063MdVz0erk9VXVJdDH3Me2toA2uTZoqOYAF5SJFRfBApDP770C4yytOhjXHx0m7lWBaN8ZIRHLyfcRPlTl31lpjHvxb6nSdV16TZKDi4gwP8GtoDoswoPoj1ko+WP1WbQ5tw3imNdEDYepoiBxMl3YSxYoDlSb9HhFOXYmM4pGfSNPXTOSSNNMX8D6omNC4PjDKj8Oc/iA2cmsBDx4sVOhbbOSDmHTWx3zAwhwghBXYTHGqO5Gshc2FesT7UxYwyOfssimwMQL1wBzwijVQ1SyxSBk2ZUZwfpeFVFPC00AMTX5zJo+oJ1fN37zBPe0aKJzvckPdZ3Fhr6mL11Rf8M7E5F433w0zOFtVXoV1TvRzaHdGfURggAz0nDcPskv5DlPRFBPkEX1H9LWbgE35Tl5gmloLZnvv4YIfqjdCmLv4j7e2iWJ9a9p21uar6WmwnGp/RFmVGSUOVz1elOeyLIMWxpQQKPZPz4k+RjRuBFLbg7P/bEWnzJftZW3wj5mQvpBcKwLHqYuvDOhVBFG3LPmG2WDbxNcMopPCOKDMKRa1o98WCxwKZgqfEQyJGiBNjwCsal4cNP+zNDH0PZ5+M6bRqWbjWjlEWSX4jw3kvrs2zYlvrjigzyslMKTwo7kAinG7TLSFRkU6s6HlDCeeRw0kfW+Sz4TuLSeF2fG3iwThC7dwk+fTUK3mj8L/xP9uizCgfiaWvFO69nHZm4DV4T4SBpZFS9gbhXsPzSCnsAv0Nw0axVNaX3cMCvy/5oj5X7KDcqqaQDdLa+q40R8qp0C6FhfXCnSp6dC3ro0DjBX+olkpx8WIn05N2ZmBcnsnv8Nr0LcFQ4SkonaOLOTnslqg3n4sVaV7HvB2uR9j2x7cBjm9wHsvaOGnRu7FBwysTBsDJuNXhikH8lHYGKHgU+31iNel+hXPYx2JzTaMgsldaOxaZ4YKYcd8T2+hUVFRUVFRUVFRUVLTmPxBM6ubCfoF0AAAAAElFTkSuQmCC>

[image51]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAYCAYAAACWTY9zAAAB80lEQVR4Xu2VzytFQRTHv0JRRFFSpGRjYUXKwtLKSiyQnYWNFUX+AHs2lJQs/AeUbNy1jR9LUUgpJRuUhR/n+2bm3Xnn3Xfnvmws7qe+NXNm5t4z58yZAXL+D52iBm1UNItqtTFEqzYITdqQwIrow7aHRVuitni4AJ2ZEC0rexB+8FUbhV3RpmhaNKXUb+c8io5sm3yLPkXziOfeiH6QbaNFamAWUT4doltvTKvHzmN71bbJGWKnHZeiOWULMip6Qblj/PgdzNmhuAHC+Q+2TbRjF6JBr18n2hPVe7YgGzCLIpQ7NgOTRp9G0Q5Kf8LUHXj9U8QpY1QZrarhIi6OUO6YhhHjQdcH+wQm5aQFccroPDe9bfuZYHi5wO08QtixSHSsjRYXyVnPRmeZdgevkiEEUjopOvf6EcKOcXxBGyvAVK4hPpfjojeYf7I4EqHHPFtuEYmQ7tiI6B6mCELw6rn2+szOO+KCYLX7xVGExmeYynL6gnGM7SvRQHG2YR3G+Sz3UITSi5SO+JtiQLJGvrCwUsR6RU8wledHOYkxUZ+yMRA62v71kkqaY/wwU7GvBxRdSL4aaNcRW4qHk+HP6JAv/zwQni8+MXye0nBXTxI8KoySu3JYxX+GDzCruF0PeHTDpLESizAbPkRpYeTk5ORUyy95RmoMtDTVAQAAAABJRU5ErkJggg==>

[image52]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADYAAAAYCAYAAACx4w6bAAAC2UlEQVR4Xu2WTahNURTHl1BEPstH6MnEUBJSzBgyQCGSEQZIFBGlZICJJEr0MpDyMZKBj/KSIkopolAvJaUQM+Rj/Vp7u+uuc8859/XMnF/9u2evve/Ze6291t5HpKFhsAxVTVINiR2BUdEwGMZFwz+mR3VVNVJ1VvVWzFEPTl9TTQ/2UnjBM9Xv9LtRbIIMEbqjOqJa3UHTWkNL6VV9V71TbQ99cEi1ND1PVr0QG3tUbI71qp9JXbFb9SjYFqg+Sysl5qi+ijneSWPTuE6sElsM0c5sUJ1RDUvtWar3qql/R4jsdc+Zh6qJ0VjGY9XxYMOhi2KRAyLZLzaxn5wFEtkq6Md5D6n0TbUotXPgqhybq1oYbJW8EZt4jLMRFXZxRGoflGL6sAN7pL7Q8656RifbjdRmHp7nu/676RmY57Zrd8UlsUm+qNaphovl+yc3JsIYCpzfOqocI6iZFap9YoEife+5PsaxYwNmirQW8Eu1X9oPj8gr1aloLIFajY5RU9hIP89s1bH0Czh5QloBpD1TWiVSCynwWmzXsoPUXhk4n0+wOjgkeF8+KGBTskXHIuzic9e+IrbGj6ptUlMGRLTXtbOTTMyfI2tVfWLp1C1kBMH4ILbQJVIfvJjuHDSsMzvD2vy6C/xQLQ42jm/uLS5MH2mesV1wtm4hEJx6LHS8mGNVC1sj7RfxLmk/KdmAB67dBgvl/iDnI7z0XLARAAJBDZbBael3c6eYE/6uI8X4EPB3m+e66nCwEUzvGOvzB0wBJt0ajcpK1bJgWy42Pt4xGQJFP+mduZls81Ibp2+JnXxl9Enx0ieYcceeuHaBCarLYnV1XvVSrB4O+EEJ6otFkhadIP/5yrjvbD1iu0PEEZ9VO1y/B2e4rzodCgSE03iG2DufSjHwBXjRFrFi5Wui7LOFK2CzDPzrmro6qTot1f9lR0jDMjhsCHy/WOB9/Tc0NDQ0/F/8ARYgmbSQbKuxAAAAAElFTkSuQmCC>

[image53]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADYAAAAYCAYAAACx4w6bAAAC8klEQVR4Xu2WTahNURTH/0IRUZSP0JOUmEhCyhBDyUeIpCSSEUX0BldGmMiAEkmSfI2kFPFCEaUUkY96lGSAKAbkY/2svd/dZ597r/t6Bsr51b9z9tr7nLPX2mvtfaSKir7S3zTK1C/vyBiSG/5lOkznTYNNR0yv5I6m4PQF0/jM3hRe8ND0M1zXyj/QiGmmr/KxG1T+eCN41xP5M92m3YVep2aaH+5Hmx6bXpv2mpaZVpu+B7XFNtPdzDbb9EHFlBgon9j20B4e2jd7RjTmsOlq0mZlngZxD5NMb0xj4yBjR3IfuWMamRubcc+0P7Ph0Cl55CJrTJdVX0n6cIznW/HO9FbFIG2RP1sL7emmT2rt2AzTnMzWkhfyjwxLbESFVRwU2ivlY2b2jGgfnOLZNNI4gK0rtPnOJdOs0B5quh7ugSy5krTb4rT8Ix9Nq+QpVzO9T8YcDWPGyaNGce9L+lsx2bQ4s+EA78OZyCLTTvnKLjXdSPoIPivWa8bIP4R+mHapuHm8DH3X5LUF9GMjRXsDOxsbFHUX3xWZIg8YV8DJA/Jgx/ZEFUukJUTwuXzVooNp7UTHSMkUbM8y25/YI3+uI+9oAKv4KGmfk8+RuqVOW5537H7Hk3Z0ko/zMOAk7bS4IQahXZaYTqq9A5ZVIuXjas2VzzM6w9zSeZf4ZpqX2UgRUoUDc4C8FvrqGEcIdRsnynVEvbvEChUP4q0q7pQswO2kXYBJc35wjuTwUjYN4OCk9qbWu3+DU9hTqCF2tRTSbp2KqUMdn0jaKRflKZvC2NQx5pduMCWY3KbcKE+bBeGeiXbJcz6FZ7FHCBQ20juCUxzGm+V/EOtNh+QBzc+qSJfKGwuByFfsftIuQTqcldfVMfmvD6vQmQ6SR5vCRWdMX1Q/dyKM4ZfnVmKL6Zrrs8rnIs5wXjXaFAguG9UEebAeqB74pvCijfJiZftu9ttC0S83HTQtzPr+BqwIadgMNjEC3y0PPBlSUVFRUfF/8gvb/qH1fNgzmgAAAABJRU5ErkJggg==>

[image54]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGUAAAAYCAYAAADjwDPQAAAEVUlEQVR4Xu2YS6hWVRTHV5igUKYlWqB4CR2IUoqPahCKJBiS4AN8ggMHNtCJYkI0UKRBjVQkwQcXA8nEQKjAx0BQUXGgBIriA0rMINAwTLDIWj/XXvess79z8LvIvR/C+cGfe/Y++35n77XWXnudI9LQ0NBZXlINyjszXlYNyDufQ0aoXss7MwbmHf3JJ6qHqlmq6ap70jphHDFftT7rf94Yo7qmGixm9Fuq2aURxneqK3lnOwxR/az6T3VOtUzsYTlrxcb9qzqteqF0V+S26kcpdska1SPVUdWipBtiz2E3dYLjqhWqN5LGqS6o5sRByijVA7G57k7tyCbV49DG8P+ovhBb53LVt2K2mhfGtcX3Yl52A78nZkgm82Lq4+9O1eLUBqIjfyD/szG0WfT40IafxIzSKZhj1O/SmkYx8M3QHqu6I4Vj3lT9pvqlZ4Ste3tow8fSminagh9mcm48DOl9XIM7anhqO4w5krVzp0wJbZzbLZ3NsQThR2LRzJpzhwDriAYmYJk3Ox/eVv0prU7ZF9qTpezYXjFGtTK0p4mdC0zM0xApiXaerpgY/Q7beb8U49hFnqZ4Druk00TDVYGjWNOCrH+d2O5gl2AXbIKdnBNSZA3WT5p8pbj9bGwRm9Qfoe9y6svxHeUcE4uOLrEJMTGHSCMFdhp3ysyk/Gz7QGxN7KYIbZxA0AIOIH17AJ6UIlW9I7ZTnhk/1M5I66GWG9+p6qdAoFCIxcIE1fs9IyzSpkpn0hjz3ZyuMSjn5CWxnQwYv84pVf1fJjlbVQdDu0v1YWj3CuptzoCLqr9VG8K9KuNDXX+ESGQHeUTNFQsAnnPeB/Uj26QcDMyPNfgurjN+XX8OWaUrXZMt7qsOi51HboNewz9yLjCBJamvzvh1/RFqed5ZgIP+LykO/5HhugpKcCrDdkTazMvadmENvo4643t/XdTj6F3pL3hx5I7AKd3p+qkMTYpQSTCBQ2KGPJXaORx8Vf0OkRJfEnECjvSqjgmvLm73OW+pvpLWAzg6hTOjyim8d8SAyiENxkKGwiDaht89G9q1+NbNDUs5SN+e1GZCtIf1jDCotnhhrIK327wkZEHRKRBL6L7EMwCGfTe7x9rupmuCkPbnxe0nYJNvpHh3i3B2UiDF9LRPynblnKYYeCr8SO4UHsC7B33+2WC06rpqog9KMGZH1ucQNfFlE5hYvlOIqP6CFBIDAqiYWEesDAm2+P7lNqlLj2SDfPd9Kq07hS8HbTFD7NMHhxE5kR/icFoaB4m9ZFECckB/JjZmUmlEwUIpqpkcfoPdgUP4Vlb1Oacvobqk3CeSfxVb7+ulESKvin2z+losS+CkA6URBZT9rCPHCxwCGgjSqm9jtWDwzWJOoU6v+8JLVK0SKwGpxatgEpSYdRCtpJAfxIqA/oa1MnfWynnWVbpbQNC4TdywVfCFoC6wyAxXVXvFArkq9TU0NDQ0NDQ0NDQ0FPwPndH8T/MzV+EAAAAASUVORK5CYII=>

[image55]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEIAAAAZCAYAAACFHfjcAAACc0lEQVR4Xu2Xz0sVURTHj6RQJIQGQRCISoG0sCgCw0ULC0JsYRIt3QUSLotaRIv6B9oE4rZtuYl+Lh64qRQMEYrAhW4EQyLIwKQf329nTu/MkbGXvDdt7gc+zJszd2buPXfujyeSSCQStXEQfoI/4Wt4MX/5N4PwCjwsWr4DvoDjvlCD4XtfwVPZbzoAH8K9rtwueEm0PXQhi23LSbgCT8MzUr15nytDrrtr5jPY7gs1mBNwXbbWo88XAhPwu2hy6A14H7b4QhE+aM6d74FP4YbkXzAEh+GIaPK2fWiD4BcwL1oHGjuLdMI12BPiTOC7EMthWW12Met9Hg0motWd/w+YiLcxGLgMl0TLehhjmwrph2dD7KboTZwTDEvEbngO7nfXysISwfHenenHPuv2GFZka6cxxjY1hXghNjQ+wqMuzkTcEf3sWJkf8Ii7XgY2NN6L9vA3uCrVxrHxlcyiRMR4IW9Eb4hzAGdnPyb5cpZ77mKN5gB8EmIXRFe841LHRLDxLHw7xItgWX4ZRfCltszVIj/tf6VXtB73pE6JuAa/uHPeYDcdgo+yo8cm2rK4BWdDjAlkHSqiX+mD7Hds8IzUUFc+gHsJLovGpFRXjbuiD+HRU3YiNkXf1+ZiPhGEdd7RqkG4k4zr7rToBElsFeFuzfO3oVFvvoq+0y/13GTZ0CBcBdmpXX9KKJzkN0Ish22toz6rnDu4W7NdJL+gUbgMj2WxMmCHfXDn7LxFeFXyyyJ3lS/dOSd5tpNb80JiAsyK5McZH8aMTokuXyxT9vLJxo6JjnfbRn/O4h6uJNxJ8n8QZaeez5VIJBKJRCKRqAO/ACjnmp2RUG/tAAAAAElFTkSuQmCC>