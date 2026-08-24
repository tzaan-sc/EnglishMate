import sys
from app import create_app
from app.extensions import db
from app.models import ToeicTest, ToeicPassage, ToeicQuestion

PART_5_QUESTIONS = [
    {
        "num": 101,
        "text": "Edison Delivery's trucks leave the warehouse promptly _______ 6:00 A.M. each morning.",
        "a": "(A) at", "b": "(B) on", "c": "(C) for", "d": "(D) with",
        "ans": "A",
        "exp": "Trước thời gian cụ thể trong ngày (6:00 A.M.), ta dùng giới từ at."
    },
    {
        "num": 102,
        "text": "A _______ copy of the rental agreement for the apartment has been delivered to the main office.",
        "a": "(A) signature", "b": "(B) sign", "c": "(C) signs", "d": "(D) signed",
        "ans": "D",
        "exp": "Cần một tính từ/quá khứ phân từ đứng trước danh từ copy để bổ nghĩa: signed copy (bản sao đã có chữ ký)."
    },
    {
        "num": 103,
        "text": "_______ can be made online or by calling customer service between 6:30 A.M. and 5:30 P.M.",
        "a": "(A) Reserve", "b": "(B) Reserved", "c": "(C) Reservations", "d": "(D) Reservable",
        "ans": "C",
        "exp": "Đứng đầu câu làm chủ ngữ trước động từ can be made cần danh từ số nhiều: Reservations (việc đặt chỗ)."
    },
    {
        "num": 104,
        "text": "Ms. Shimabukuro rose through the ranks _______ and became the manager in less than two years.",
        "a": "(A) quick", "b": "(B) quicken", "c": "(C) quickly", "d": "(D) quickening",
        "ans": "C",
        "exp": "Cần trạng từ quickly bổ nghĩa cho cụm động từ rose through the ranks (thăng tiến nhanh chóng)."
    },
    {
        "num": 105,
        "text": "The Highland Museum of Robotics will be _______ for renovations until further notice.",
        "a": "(A) bought", "b": "(B) closed", "c": "(C) stopped", "d": "(D) held",
        "ans": "B",
        "exp": "Cụm từ cố định closed for renovations (đóng cửa để sửa chữa/trùng tu)."
    },
    {
        "num": 106,
        "text": "The Hollytown Arena designates an area where fans can meet their _______ athletes after each game.",
        "a": "(A) favorite", "b": "(B) favoritism", "c": "(C) favorites", "d": "(D) favoring",
        "ans": "A",
        "exp": "Cần tính từ favorite bổ nghĩa cho danh từ athletes (những vận động viên yêu thích)."
    },
    {
        "num": 107,
        "text": "Billboards that advertise legal services are most effective when placed _______ business districts.",
        "a": "(A) from", "b": "(B) down", "c": "(C) of", "d": "(D) in",
        "ans": "D",
        "exp": "Vị trí địa lý/khu vực thương mại dùng giới từ in: in business districts (tại các khu thương mại)."
    },
    {
        "num": 108,
        "text": "Ms. Ueda was quite _______ with the wholesale prices offered by Rea's International Restaurant Suppliers.",
        "a": "(A) advised", "b": "(B) true", "c": "(C) pleased", "d": "(D) strong",
        "ans": "C",
        "exp": "Cấu trúc be pleased with something (hài lòng với điều gì)."
    },
    {
        "num": 109,
        "text": "Geology Monthly is a professional journal with articles written _______ for experts in the field.",
        "a": "(A) specify", "b": "(B) had specified", "c": "(C) specifics", "d": "(D) specifically",
        "ans": "D",
        "exp": "Trạng từ specifically bổ nghĩa cho quá khứ phân từ written (specifically written for - được viết đặc biệt dành riêng cho)."
    },
    {
        "num": 110,
        "text": "_______ the year-end sale at Arthur's Camping Supplies, all winter items are discounted by 25 percent.",
        "a": "(A) During", "b": "(B) Although", "c": "(C) As long as", "d": "(D) In addition",
        "ans": "A",
        "exp": "Đứng trước cụm danh từ the year-end sale chọn giới từ During (trong suốt đợt giảm giá cuối năm)."
    },
    {
        "num": 111,
        "text": "In the _______ future, a hardware store will open on the corner of Oak Boulevard and Primrose Avenue.",
        "a": "(A) nears", "b": "(B) nearly", "c": "(C) nearness", "d": "(D) near",
        "ans": "D",
        "exp": "Cụm từ cố định in the near future (trong tương lai gần)."
    },
    {
        "num": 112,
        "text": "Mr. Careni requested that _______ from the technical support team come immediately to the Harrisburg office.",
        "a": "(A) who", "b": "(B) someone", "c": "(C) which", "d": "(D) themselves",
        "ans": "B",
        "exp": "Cần đại từ làm chủ ngữ trong mệnh đề that: someone from... (ai đó thuộc đội hỗ trợ kỹ thuật)."
    },
    {
        "num": 113,
        "text": "The time-entry system was _______ unavailable this afternoon, but it is functioning normally now.",
        "a": "(A) directly", "b": "(B) urgently", "c": "(C) precisely", "d": "(D) briefly",
        "ans": "D",
        "exp": "Ngữ cảnh gián đoạn ngắn: briefly unavailable (tạm thời không khả dụng trong thời gian ngắn)."
    },
    {
        "num": 114,
        "text": "The upcoming career fair _______ by more than 100 employers and job-recruiting agencies.",
        "a": "(A) attend", "b": "(B) were attended", "c": "(C) was attending", "d": "(D) will be attended",
        "ans": "D",
        "exp": "Hành động trong tương lai upcoming và ở dạng bị động by...: will be attended (sẽ được tham dự bởi)."
    },
    {
        "num": 115,
        "text": "_______ theater at Landon Cinema is decorated with a different theme.",
        "a": "(A) Even", "b": "(B) Much", "c": "(C) Each", "d": "(D) All",
        "ans": "C",
        "exp": "Each đi với danh từ đếm được số ít theater và động từ số ít is."
    },
    {
        "num": 116,
        "text": "Changes to course content have been halted _______ the Salinas Academy transitions to a new online platform.",
        "a": "(A) while", "b": "(B) though", "c": "(C) regarding", "d": "(D) whether",
        "ans": "A",
        "exp": "Liên từ chỉ thời gian while + mệnh đề (trong khi Salinas Academy chuyển sang nền tảng mới)."
    },
    {
        "num": 117,
        "text": "Bricktown Mayor Julian Trent will _______ help plant flowers in Evans Park this weekend.",
        "a": "(A) personal", "b": "(B) personalize", "c": "(C) personally", "d": "(D) personality",
        "ans": "C",
        "exp": "Trạng từ personally đứng trước động từ help để bổ nghĩa (đích thân giúp đỡ)."
    },
    {
        "num": 118,
        "text": "Please replace pages 28 to 35 in the employee handbook with the _______ pages.",
        "a": "(A) careful", "b": "(B) updated", "c": "(C) consistent", "d": "(D) sizable",
        "ans": "B",
        "exp": "Về mặt nghĩa: Thay thế các trang cũ bằng các trang đã được cập nhật (updated pages)."
    },
    {
        "num": 119,
        "text": "_______ we increased our Internet speed, we can download large documents much faster.",
        "a": "(A) Since", "b": "(B) Provided", "c": "(C) Yet", "d": "(D) Instead",
        "ans": "A",
        "exp": "Since đứng đầu câu mang nghĩa nguyên nhân: 'Vì/Bởi vì chúng tôi đã tăng tốc độ Internet...'."
    },
    {
        "num": 120,
        "text": "The lead graphic artist decides which photographs submitted by freelancers _______ to the creative director.",
        "a": "(A) are sending", "b": "(B) sender", "c": "(C) should be sent", "d": "(D) send",
        "ans": "C",
        "exp": "Mệnh đề danh ngữ làm tân ngữ: which photographs... should be sent (những bức ảnh nào nên được gửi đi - dạng bị động)."
    },
    {
        "num": 121,
        "text": "_______ you visit the Star Hotel, the cheerful staff makes you feel welcome.",
        "a": "(A) Whenever", "b": "(B) Whichever", "c": "(C) Nevertheless", "d": "(D) Altogether",
        "ans": "A",
        "exp": "Whenever + mệnh đề: 'Bất cứ khi nào bạn ghé thăm khách sạn Star...'."
    },
    {
        "num": 122,
        "text": "Ms. Matlou considered a legal career before _______ deciding to go to business school.",
        "a": "(A) strictly", "b": "(B) politely", "c": "(C) ultimately", "d": "(D) slightly",
        "ans": "C",
        "exp": "Trạng từ ultimately chỉ kết quả sau cùng (cuối cùng đã quyết định học trường kinh doanh)."
    },
    {
        "num": 123,
        "text": "Patrons of the festival enjoying picnic lunches on the concert hall's lawn is a _______ dating back almost a century.",
        "a": "(A) traditional", "b": "(B) tradition", "c": "(C) traditionalist", "d": "(D) traditions",
        "ans": "B",
        "exp": "Sau mạo từ a cần danh từ đếm được số ít: a tradition (một truyền thống)."
    },
    {
        "num": 124,
        "text": "Many people _______ their online shopping carts when they discover what the shipping charge will be.",
        "a": "(A) eject", "b": "(B) abandon", "c": "(C) resign", "d": "(D) discourage",
        "ans": "B",
        "exp": "Cụm từ thông dụng trong thương mại điện tử: abandon shopping carts (bỏ dở/từ bỏ giỏ hàng)."
    },
    {
        "num": 125,
        "text": "The state's tourism Web site provides information on many of the area's popular _______.",
        "a": "(A) situations", "b": "(B) appeals", "c": "(C) demands", "d": "(D) attractions",
        "ans": "D",
        "exp": "Cụm danh từ du lịch: popular attractions (các điểm thu hút du khách nổi tiếng)."
    },
    {
        "num": 126,
        "text": "_______ interested in learning more about Shana Fabian's sculptures should attend her talk at Deana Gallery on May 2.",
        "a": "(A) Enough", "b": "(B) Whoever", "c": "(C) Each other", "d": "(D) Those",
        "ans": "D",
        "exp": "Those interested in... là dạng rút gọn của Those who are interested in... (Những ai quan tâm tới...)."
    },
    {
        "num": 127,
        "text": "The merger between the Oznaze and Tellurisq companies was _______ settled following months of tough negotiations.",
        "a": "(A) exactly", "b": "(B) instantly", "c": "(C) finally", "d": "(D) easily",
        "ans": "C",
        "exp": "Sau nhiều tháng đàm phán gay gắt, vụ sáp nhập 'cuối cùng' (finally) đã được giải quyết."
    },
    {
        "num": 128,
        "text": "Auto parts are shipped _______ two to three days unless the customer requests expedited delivery.",
        "a": "(A) within", "b": "(B) here", "c": "(C) afterward", "d": "(D) perhaps",
        "ans": "A",
        "exp": "Giới từ chỉ khoảng thời gian: within two to three days (trong vòng 2 đến 3 ngày)."
    },
    {
        "num": 129,
        "text": "The interior designer selected some very _______ colors for the lobby walls.",
        "a": "(A) massive", "b": "(B) intense", "c": "(C) direct", "d": "(D) sudden",
        "ans": "B",
        "exp": "intense colors mang nghĩa màu sắc đậm, rực rỡ, mạnh mẽ."
    },
    {
        "num": 130,
        "text": "Experts recommend that the cooling system be checked by a service technician at regular _______.",
        "a": "(A) expanses", "b": "(B) intervals", "c": "(C) classifications", "d": "(D) detachments",
        "ans": "B",
        "exp": "Cụm từ cố định at regular intervals (theo định kỳ / ở những khoảng thời gian đều đặn)."
    }
]

PART_6_PASSAGES = [
    {
        "id": 1,
        "text": "To: Roger Wall <rogerwall@openemail.com>\nFrom: Guillermo Torres <gtorres@supplyflow.com>\nDate: May 2\nSubject: RE: Missing delivery\n\nDear Mr. Wall,\n\nThis is in response to your [131] e-mail notifying us that you did not receive your April shipment of office supplies. We verified that your annual subscription is up-to-date and that everything is in order on your side. This error is, therefore, an oversight on [132] part. We have transitioned to new shipping software, and some customer information was not transferred correctly. Rest assured that this has been fixed and that the error will not [133] again. We sent your box of office supplies today using an overnight shipping service. [134]. Inside the box, you will also find a complimentary token of appreciation for your patience.\n\nSincerely,\n\nGuillermo Torres\nCustomer Assistant\nSupply Flow, Inc.",
        "questions": [
            {
                "num": 131,
                "text": "131.",
                "a": "(A) constant", "b": "(B) nearby", "c": "(C) early", "d": "(D) recent",
                "ans": "D",
                "exp": "'...in response to your recent e-mail' (hồi đáp lại email gần đây của ông)."
            },
            {
                "num": 132,
                "text": "132.",
                "a": "(A) either", "b": "(B) its", "c": "(C) our", "d": "(D) their",
                "ans": "C",
                "exp": "Cụm từ an oversight on our part (một sơ suất về phía chúng tôi)."
            },
            {
                "num": 133,
                "text": "133.",
                "a": "(A) combine", "b": "(B) revise", "c": "(C) affect", "d": "(D) occur",
                "ans": "D",
                "exp": "'...the error will not occur again' (lỗi này sẽ không xảy ra lần nữa)."
            },
            {
                "num": 134,
                "text": "134.",
                "a": "(A) You should receive it tomorrow.", "b": "(B) This order will take longer than usual to process.", "c": "(C) The box is very heavy.", "d": "(D) Please review the invoice attached to this e-mail.",
                "ans": "A",
                "exp": "Câu trước nhắc tới dịch vụ chuyển phát nhanh qua đêm (overnight shipping service), nên câu tiếp theo logic là 'Bạn sẽ nhận được nó vào ngày mai'."
            }
        ]
    },
    {
        "id": 2,
        "text": "To: Marketing Department, Tavola Foods Distributors\nFrom: Victor Cotillo\nDate: March 4\nSubject: Information\n\nPlease look at the proposed survey that was just added to our team folder. The first section asks [135] to rate their favorite vegetables. We felt shoppers might prefer a particular vegetable only if it is fresh and in season. [136], we also ask what frozen vegetables they buy most frequently and why. In addition, we [137] a series of questions about food preparation and convenience. We feel this survey will give us a better picture of what our customers want. Please look over everything and quickly respond with any thoughts. [138].",
        "questions": [
            {
                "num": 135,
                "text": "135.",
                "a": "(A) farmers", "b": "(B) executives", "c": "(C) consumers", "d": "(D) merchants",
                "ans": "C",
                "exp": "Khảo sát người mua hàng/người tiêu dùng (consumers)."
            },
            {
                "num": 136,
                "text": "136.",
                "a": "(A) In effect", "b": "(B) Therefore", "c": "(C) On occasion", "d": "(D) Nevertheless",
                "ans": "B",
                "exp": "Từ nối chỉ kết quả: Do đó/Vì vậy, chúng tôi cũng hỏi về rau đông lạnh."
            },
            {
                "num": 137,
                "text": "137.",
                "a": "(A) were inserting", "b": "(B) have inserted", "c": "(C) had been inserting", "d": "(D) could have inserted",
                "ans": "B",
                "exp": "Thì hiện tại hoàn thành diễn tả hành động đã hoàn thành trong bản khảo sát vừa tạo."
            },
            {
                "num": 138,
                "text": "138.",
                "a": "(A) We want to start distributing the survey next week.", "b": "(B) We value the feedback provided by you, our customers.", "c": "(C) Despite higher costs, demand for our products has risen.", "d": "(D) As we all know, fresh vegetables are good for you.",
                "ans": "A",
                "exp": "Phù hợp ngữ cảnh yêu cầu đồng nghiệp phản hồi nhanh để kịp phân phát bài khảo sát vào tuần tới."
            }
        ]
    },
    {
        "id": 3,
        "text": "To: vendors@grovecenterfleamarket.org\nFrom: alanc@spicebest.com\nDate: October 22\nSubject: Parking issue\n\nDear Vendors,\n\nStarting next month, the owners of the Grove Center Flea Market will charge a flat daily rate of $10 to use the onsite parking deck. This means customers who drive to our weekly flea market will no longer enjoy free parking. I'm concerned that this might [139] some shoppers from coming, which will hurt our businesses. As president of the Grove Center Flea Market, I have asked the owners to consider waiving or reducing the fee. [140]. The nearest other large-scale parking facility is at city hall, three long blocks from our site. Street parking is available but can be [141] to find. Please reply to all if you have any thoughts on alternative [142].\n\nBest,\n\nAlan Coleman",
        "questions": [
            {
                "num": 139,
                "text": "139.",
                "a": "(A) remove", "b": "(B) carry", "c": "(C) discourage", "d": "(D) manage",
                "ans": "C",
                "exp": "Cấu trúc discourage someone from V-ing (làm nản lòng/ngăn cản khách hàng tới)."
            },
            {
                "num": 140,
                "text": "140.",
                "a": "(A) Their offices are not open on Sundays.", "b": "(B) I also asked them to expand the garage.", "c": "(C) Nevertheless, we have more vendors than last year.", "d": "(D) Unfortunately, we could not reach a compromise.",
                "ans": "D",
                "exp": "Tác giả đã xin miễn/giảm phí nhưng 'Thật không may, chúng tôi không thể đạt được thỏa thuận'."
            },
            {
                "num": 141,
                "text": "141.",
                "a": "(A) difficult", "b": "(B) pleasant", "c": "(C) expensive", "d": "(D) specific",
                "ans": "A",
                "exp": "Đỗ xe dưới lòng đường thì có sẵn nhưng 'khó tìm' (difficult to find)."
            },
            {
                "num": 142,
                "text": "142.",
                "a": "(A) solution", "b": "(B) solutions", "c": "(C) solve", "d": "(D) solving",
                "ans": "B",
                "exp": "Sau tính từ alternative cần danh từ số nhiều solutions (các giải pháp thay thế)."
            }
        ]
    },
    {
        "id": 4,
        "text": "QUEENSVILLE (November 3)—Recycling just became easier for many local residents thanks to the opening of the township's second recycling center. \"West Queensville residents now have a more [143] location to drop off their materials,\" Mayor Dustin Larson said at yesterday's ribbon-cutting ceremony. \"No longer must they travel to the east part of the town.\" [144]. However, Ida Aguirre of the Queensville Clean Coalition criticized the town council's decision to eliminate curbside pickup of recyclables. \"Curbside pickup should be resumed [145] elected officials want to make recycling easier,\" she said in a telephone interview. Open 6 A.M. to 8 P.M. on weekdays, the new 18 Darren Street facility takes only mixed paper and some plastics. Aluminum is not currently [146].",
        "questions": [
            {
                "num": 143,
                "text": "143.",
                "a": "(A) widespread", "b": "(B) convenient", "c": "(C) ordinary", "d": "(D) stable",
                "ans": "B",
                "exp": "Mở trung tâm tái chế thứ 2 giúp cư dân có vị trí thuận tiện hơn (convenient location)."
            },
            {
                "num": 144,
                "text": "144.",
                "a": "(A) The percentage of household waste sent to landfills has decreased recently.", "b": "(B) Those who attended the ceremony applauded the new facility.", "c": "(C) Employees at both drop-off sites can help unload materials.", "d": "(D) The drop-off site in West Queensville opens next year.",
                "ans": "B",
                "exp": "Nối tiếp câu trích dẫn của Thị trưởng tại lễ cắt băng rôn: Những người tham dự buổi lễ đã hoan nghênh cơ sở mới."
            },
            {
                "num": 145,
                "text": "145.",
                "a": "(A) by", "b": "(B) so", "c": "(C) if", "d": "(D) through",
                "ans": "C",
                "exp": "Liên từ điều kiện if: '...nên được khôi phục nếu các quan chức muốn việc tái chế dễ dàng hơn'."
            },
            {
                "num": 146,
                "text": "146.",
                "a": "(A) accepted", "b": "(B) accepting", "c": "(C) accepts", "d": "(D) accept",
                "ans": "A",
                "exp": "Dạng bị động: Nhôm hiện chưa được tiếp nhận (is not currently accepted)."
            }
        ]
    }
]

PART_7_PASSAGES = [
    {
        "text": "Questions 147–148 refer to the following e-mail.\n\nTo: Jeanne Vasseur\nFrom: Milo Bailey\nDate: 4 February\nSubject: Information\n\nDear Jeanne,\n\nI think we made the right decision in hiring Carol. She has some excellent ideas about design and content for our Web site. The new site she created will help us attract new clients and help our current clients get the information they need. In addition to the minor changes you suggested earlier, we could have a blog on the Web site to post accounting tips and share some anecdotes. We need to sit down with Carol to share our thoughts. Her schedule is open tomorrow morning—will you be free?\n\nSincerely,\n\nMilo",
        "questions": [
            {
                "num": 147,
                "text": "147. Why did Mr. Bailey send the e-mail to Ms. Vasseur?",
                "a": "(A) To inquire about a product", "b": "(B) To explain a new process to her", "c": "(C) To discuss changes to a Web site", "d": "(D) To ask her to contact a new client",
                "ans": "C",
                "exp": "Milo viết email để bàn về ý tưởng thiết kế trang web mới mà Carol vừa làm và đề xuất thêm blog."
            },
            {
                "num": 148,
                "text": "148. What does Mr. Bailey want to do?",
                "a": "(A) Review a schedule", "b": "(B) Hire additional staff", "c": "(C) Open a new account", "d": "(D) Meet with a new employee",
                "ans": "D",
                "exp": "Milo muốn ngồi lại họp với Carol (nhân viên mới được tuyển) vào sáng mai."
            }
        ]
    },
    {
        "text": "Questions 149–150 refer to the following receipt.\n\nGreen's Athletic Shoes\n18502 Oriole Avenue, Chicago, IL 60800 | (312) 555-0132\nAugust 5, 11:27 A.M. | Receipt number: 5926\n\nLunarwave running shoes, Style: Fleetfoot, men's size 10 .......... $119.00\nSuresocks cotton running socks, men's size large .......... $4.99\nCoolbreeze T-shirt, men's size medium, Regularly $14.00, now 15% off .......... $11.90\n\nSubtotal: $135.89 | Sales tax (6.25%): $8.49 | Total: $144.38\n\nThank you for shopping at Green's Athletic Shoes! Please fill out a customer survey at www.greensathletic.com. All returns must be made within 30 days. A receipt is required to make a return.",
        "questions": [
            {
                "num": 149,
                "text": "149. What is indicated about the T-shirt?",
                "a": "(A) It was made by Lunarwave.", "b": "(B) It is a size large.", "c": "(C) It is made of cotton.", "d": "(D) It was sold at a discounted price.",
                "ans": "D",
                "exp": "Hóa đơn ghi: 'Coolbreeze T-shirt... Regularly $14.00, now 15% off' (đang giảm giá 15%)."
            },
            {
                "num": 150,
                "text": "150. What must a customer do to return an item?",
                "a": "(A) Complete an online form", "b": "(B) Bring the item back within six months", "c": "(C) Show an original store receipt", "d": "(D) Mail the item to the manufacturer",
                "ans": "C",
                "exp": "Hóa đơn ghi rõ: 'A receipt is required to make a return.'"
            }
        ]
    },
    {
        "text": "Questions 151–152 refer to the following text-message chain.\n\nMonica Blanco (10:43 A.M.): Hi, Carrie. Are you working this Friday? I'm working a half shift, and I was wondering if you could cover it. My brother's birthday party is that day.\nCarrie Morgan (11:25 A.M.): I'm working a half shift too. What time are you scheduled?\nMonica Blanco (11:37 A.M.): 8 A.M. to noon.\nCarrie Morgan (11:39 A.M.): I might be able to. I could do a full day, actually. I'm scheduled after you.\nMonica Blanco (11:40 A.M.): OK.\nCarrie Morgan (11:41 A.M.): I'm at work right now. When I see Mr. Cho, I'll ask him if it is OK to do your shift as well as mine.\nMonica Blanco (11:50 A.M.): Thank you! I appreciate it.",
        "questions": [
            {
                "num": 151,
                "text": "151. At 11:39 A.M., what does Ms. Morgan mean when she writes, \"I might be able to\"?",
                "a": "(A) She could help organize a weekend event.", "b": "(B) She could work Ms. Blanco's hours on Friday.", "c": "(C) She could pick up some food for a party.", "d": "(D) She could meet with Ms. Blanco during her break.",
                "ans": "B",
                "exp": "Monica hỏi Carrie có làm thay ca làm việc sáng thứ Sáu được không, Carrie đáp 'I might be able to' (Tôi có thể làm được)."
            },
            {
                "num": 152,
                "text": "152. Who most likely is Mr. Cho?",
                "a": "(A) A temporary worker", "b": "(B) A party planner", "c": "(C) A supervisor", "d": "(D) A friend of Ms. Blanco's",
                "ans": "C",
                "exp": "Carrie nói sẽ hỏi Mr. Cho xem có được phép làm luôn ca của Monica không => Mr. Cho là quản lý/giám sát."
            }
        ]
    },
    {
        "text": "Questions 153–154 refer to the following memo.\n\nMEMO\nTo: All Avisomark Employees\nFrom: Eugenia Bajorek, Assistant Communications Director\nDate: January 30\nRe: Our company newsletter\n\nAs part of a company-wide effort to reduce waste, we will be discontinuing the print version of our weekly company newsletter, effective March 1. From that date forward, the newsletter will be published in its online format only. In addition, beginning in March, the submission deadline for the Employee News section of the newsletter will be changed from the third Friday of each month to the second Friday of each month. This change will give Markus Quimby the time he needs to process and edit submissions. The submission process remains the same: simply e-mail Markus directly at mquimby@avisomark.com.",
        "questions": [
            {
                "num": 153,
                "text": "153. Why was the memo written?",
                "a": "(A) To announce a recent decision", "b": "(B) To introduce a new staff member", "c": "(C) To describe a volunteer opportunity", "d": "(D) To invite feedback on a new practice",
                "ans": "A",
                "exp": "Thông báo quyết định ngừng bản in bản tin công ty và chuyển sang bản online."
            },
            {
                "num": 154,
                "text": "154. According to the memo, why would employees e-mail Mr. Quimby?",
                "a": "(A) To update their personal information", "b": "(B) To request a copy of a newsletter", "c": "(C) To express their opinion on the newsletter format", "d": "(D) To send in their latest news",
                "ans": "D",
                "exp": "Email gửi bài cho mục 'Employee News' trực tiếp tới Markus Quimby."
            }
        ]
    },
    {
        "text": "Questions 155–157 refer to the following article.\n\nDriverless Buses in Swansea?\n\nSWANSEA (12 May)—A consortium of city government officials and local business leaders is considering the purchase of driverless buses for some city routes. Commissioned with exploring options to improve transportation in Swansea and surrounding areas, the group recently sent three members to Malaga, Spain, where driverless buses run an eight-kilometre loop several times a day. Consortium member Gareth Elias was impressed by what he learned. Despite concerns about safety and traffic regulations, Mr. Elias could see driverless buses becoming a reality before long, but only in specific cases. \"I believe they would be particularly useful during festivals and special events,\" he said. \"I can't imagine them being on the roads every day.\"\n\nAnisha Deepak, an engineer specialising in transportation innovation, served as a technical consultant on the trip. She was struck by the complexity of the buses' artificial intelligence system, which allows them to learn as they collect data on every trip. \"Artificial intelligence makes these buses very safe in real-world situations,\" she said. \"Nevertheless, it's best to have a human operator on board at all times in case of emergencies.\"\n\nA public community forum is scheduled for 2 June to discuss the benefits and drawbacks of driverless buses. Visit the Swansea Town Council's Web site at www.swanseatowncouncil.gov.uk to learn more.",
        "questions": [
            {
                "num": 155,
                "text": "155. What is the purpose of the article?",
                "a": "(A) To explain how a new technology works", "b": "(B) To report on a group's recent activities", "c": "(C) To recruit participants for a travel forum", "d": "(D) To announce changes to a bus schedule",
                "ans": "B",
                "exp": "Bài báo đưa tin về chuyến khảo sát xe buýt không người lái tại Malaga của nhóm công tác thành phố Swansea."
            },
            {
                "num": 156,
                "text": "156. What opinion does Mr. Elias express about driverless buses?",
                "a": "(A) They are not safe under any circumstances.", "b": "(B) Traffic regulations must be revised to accommodate them.", "c": "(C) They are practical for limited purposes.", "d": "(D) They are appropriate for Malaga but not for Swansea.",
                "ans": "C",
                "exp": "Ông Elias nhận định xe buýt này hữu ích trong các dịp đặc biệt/lễ hội, không nghĩ sẽ chạy hàng ngày."
            },
            {
                "num": 157,
                "text": "157. What is indicated about Ms. Deepak?",
                "a": "(A) She recently elected to the Swansea Town Council.", "b": "(B) She collected data for a computer system.", "c": "(C) She took notes during an emergency meeting.", "d": "(D) She traveled to Malaga as a consultant.",
                "ans": "D",
                "exp": "Bài báo nêu rõ cô Anisha Deepak tham gia chuyến đi Malaga với vai trò tư vấn viên kỹ thuật (technical consultant)."
            }
        ]
    },
    {
        "text": "Questions 158–161 refer to the following job posting.\n\nMorves Laboratories of Seoul is seeking an associate research scientist who will work collaboratively with a team of other scientists within the Research and Development Division. Morves Laboratories has more than 85,000 employees in offices and laboratories in Asia, Europe, and North America who are involved in developing, manufacturing, and selling cutting-edge medicines. The Research and Development Division is responsible for achieving the company's primary goal of creating new and effective medications for worldwide use.\n\nPrimary Job Functions:\n• Design and conduct laboratory experiments\n• Perform rigorous data analysis\n• Collaborate to write detailed reports\n• Present research findings internally and externally to clients at specific meetings\n\nPosition Requirements:\n• A master's degree in biology\n• At least five years of laboratory experience\n• Excellent oral and written communication skills\n\nTo apply, submit a résumé and cover letter to www.morveslaboratories.co.kr/careers by November 10.",
        "questions": [
            {
                "num": 158,
                "text": "158. What does the job posting indicate about Morves Laboratories?",
                "a": "(A) It offers excellent employee benefits.", "b": "(B) Its workforce is primarily based in Europe.", "c": "(C) Its main purpose is to develop new medicines.", "d": "(D) It partners with another company for product distribution.",
                "ans": "C",
                "exp": "Thông báo nêu mục tiêu chính của công ty là 'creating new and effective medications for worldwide use'."
            },
            {
                "num": 159,
                "text": "159. What is one responsibility of the position?",
                "a": "(A) Analyzing information from experiments", "b": "(B) Designing safe packaging materials", "c": "(C) Operating manufacturing equipment", "d": "(D) Responding to patient inquiries",
                "ans": "A",
                "exp": "Nhiệm vụ vị trí gồm: 'Perform rigorous data analysis' (phân tích dữ liệu từ thí nghiệm)."
            },
            {
                "num": 160,
                "text": "160. According to the job posting, what should an applicant possess?",
                "a": "(A) Knowledge of medical regulations", "b": "(B) Expertise in editing medical journals", "c": "(C) A background in teaching biology", "d": "(D) Experience working in a laboratory",
                "ans": "D",
                "exp": "Yêu cầu tuyển dụng: 'At least five years of laboratory experience'."
            },
            {
                "num": 161,
                "text": "161. How should someone apply for the position?",
                "a": "(A) By visiting the company's offices", "b": "(B) By submitting a résumé online", "c": "(C) By calling a recruiting professional", "d": "(D) By e-mailing a current employee",
                "ans": "B",
                "exp": "Hướng dẫn ứng tuyển: gửi hồ sơ qua trang web www.morveslaboratories.co.kr/careers."
            }
        ]
    },
    {
        "text": "Questions 162–164 refer to the following e-mail.\n\nTo: team@rosettipasta.com.au\nFrom: valentina_rosetti@rosettipasta.com.au\nDate: 20 August\nSubject: Update\n\nDear Team,\n\nThe past several years have been fast-paced. — [1] —. Five years ago, when I began selling my homemade pasta, I never expected to need a space larger than the kitchen in my own house. How things have changed! This week, the business won a contract to supply a regional food distributor here in Eastern Australia. This achievement certainly would not have been possible without you. — [2] —. You have all worked hard to keep pace with such tremendous growth, and it was not always easy. To show my appreciation, I have decided that each of you will receive a bonus. — [3] —. With our solid team and our streamlined production process, I am optimistic that we will see our product placed on even more supermarket shelves soon. — [4] —. The future looks bright.\n\nSincerely,\n\nValentina Rosetti\nChief Executive Officer, Rosetti Pasta Company Ltd.",
        "questions": [
            {
                "num": 162,
                "text": "162. Why did Ms. Rosetti send the e-mail?",
                "a": "(A) To thank employees", "b": "(B) To present a business plan", "c": "(C) To announce a postponement", "d": "(D) To request assistance with a project",
                "ans": "A",
                "exp": "CEO viết email cảm ơn sự đóng góp của nhân viên và thông báo thưởng tiền."
            },
            {
                "num": 163,
                "text": "163. What does Ms. Rosetti express confidence about?",
                "a": "(A) The development of a new product line", "b": "(B) The potential for more company growth", "c": "(C) The success of an advertising campaign", "d": "(D) The possibility of replacing old machinery",
                "ans": "B",
                "exp": "CEO bày tỏ sự lạc quan rằng sản phẩm sẽ sớm có mặt trên nhiều kệ siêu thị hơn nữa."
            },
            {
                "num": 164,
                "text": "164. In which of the positions marked [1], [2], [3], and [4] does the following sentence best belong?\n\n\"It will appear in your accounts on Friday.\"",
                "a": "(A) [1]", "b": "(B) [2]", "c": "(C) [3]", "d": "(D) [4]",
                "ans": "C",
                "exp": "Câu 'It will appear in your accounts on Friday' (Tiền sẽ vào tài khoản của bạn vào thứ Sáu) bổ nghĩa trực tiếp cho câu ngay trước vị trí [3]: '...each of you will receive a bonus'."
            }
        ]
    },
    {
        "text": "Questions 165–167 refer to the following e-mail.\n\nTo: Sid Shepard\nFrom: Corporate Security\nDate: July 2\nSubject: Your ID badge\n\nDear Mr. Shepard,\n\nWe received your request this morning for assistance in acquiring a new physical identification badge. As your current badge was misplaced, it has been deactivated. To receive a replacement, visit the corporate security office in Paulsen Hall between 7 a.m. and 5:30 p.m. You will be required to show a form of government-issued identification. In the meantime, you can take advantage of a new corporate initiative.\n\nThe company app installed on all employees' mobile devices now includes a digital identification card that can be used to gain entry to the corporate parking garage and campus buildings. To access the digital ID card in the app, look for the \"ID Card\" tab. You can then scan your digital ID to enter all secure areas. If you have questions or need additional help, please call corporate security at 863-555-0171.\n\nThank you,\n\nHopper Technology Corporate Security",
        "questions": [
            {
                "num": 165,
                "text": "165. What is the purpose of the e-mail?",
                "a": "(A) To respond to a request for help", "b": "(B) To promote the sale of a new product", "c": "(C) To alert authorities to a security problem", "d": "(D) To announce a new company policy",
                "ans": "A",
                "exp": "Email bắt đầu bằng 'We received your request this morning for assistance in acquiring a new physical identification badge...'"
            },
            {
                "num": 166,
                "text": "166. What is suggested about Mr. Shepard?",
                "a": "(A) He first contacted corporate security two days ago.", "b": "(B) He does not use the corporate parking garage.", "c": "(C) He does not know where Paulsen Hall is located.", "d": "(D) He has the company app installed on his mobile device.",
                "ans": "D",
                "exp": "Đoạn 2 ghi ứng dụng đã được cài đặt trên thiết bị di động của tất cả nhân viên ('installed on all employees' mobile devices')."
            },
            {
                "num": 167,
                "text": "167. The word \"gain\" in paragraph 2, line 3, is closest in meaning to",
                "a": "(A) win", "b": "(B) obtain", "c": "(C) collect", "d": "(D) increase",
                "ans": "B",
                "exp": "gain entry có nghĩa là lấy/có được quyền truy cập (obtain entry)."
            }
        ]
    },
    {
        "text": "Questions 168–171 refer to the following online chat discussion.\n\nMargo Basset [9:16 A.M.]: Hi, All. Where are we with the schedule for the weekly New Assets lunch series for our new hires?\nStephan Ruess [9:18 A.M.]: We've finalized the session topics. I believe we have confirmed one speaker.\nAlban Mithat [9:20 A.M.]: That is correct. Salima Abubakar from our north suburban office agreed to take on the first session of the series.\nMargo Basset [9:24 A.M.]: Fantastic. Is she able to present on June 10 as we planned?\nAlban Mithat [9:26 A.M.]: She is, and she suggested that a panel discussion might be more engaging for her topic, renewable resources. She will moderate the discussion. I've e-mailed the three employees she suggested as panelists.\nMargo Basset [9:27 A.M.]: That sounds good. And the other sessions?\nStephan Ruess [9:28 A.M.]: So, the topics for the other six sessions will be cryptocurrencies, commodities, investments, start-ups, real estate, and virtual interfaces. I hope to have speakers for those sessions lined up by the end of this week.\nMargo Basset [9:31 A.M.]: And they'll all be held at the midtown office.\nStephan Ruess [9:32 A.M.]: Correct. Four of our seven new hires are permanently assigned to the midtown office. The other new hires will be there on session days for required training.",
        "questions": [
            {
                "num": 168,
                "text": "168. What is suggested about the New Assets lunch session on June 10?",
                "a": "(A) It will be led by Ms. Abubakar.", "b": "(B) It will be introduced by Mr. Mithat.", "c": "(C) It will feature Ms. Basset.", "d": "(D) It will include information about cryptocurrencies.",
                "ans": "A",
                "exp": "Cô Abubakar đồng ý phụ trách buổi đầu tiên (ngày 10/6) và làm người điều phối thảo luận."
            },
            {
                "num": 169,
                "text": "169. At 9:27 A.M., what does Ms. Basset mean when she writes, \"That sounds good\"?",
                "a": "(A) She is eager to attend the New Assets lunch series.", "b": "(B) She approves of Ms. Abubakar's idea.", "c": "(C) She is pleased with all the session topics.", "d": "(D) She looks forward to meeting the recently hired employees.",
                "ans": "B",
                "exp": "Margo khen 'That sounds good' ngay sau khi Alban trình bày ý tưởng tổ chức thảo luận bàn tròn của Abubakar."
            },
            {
                "num": 170,
                "text": "170. How many sessions still need speakers?",
                "a": "(A) One", "b": "(B) Three", "c": "(C) Four", "d": "(D) Six",
                "ans": "D",
                "exp": "Chuỗi có 7 buổi, 1 buổi đã có diễn giả (Abubakar), Stephan nói 6 buổi còn lại (other six sessions) đang tìm diễn giả."
            },
            {
                "num": 171,
                "text": "171. What is true about the New Assets lunch series?",
                "a": "(A) It is the main component of employee training.", "b": "(B) It will be held in the same location every week.", "c": "(C) It will consist exclusively of panel discussions.", "d": "(D) It will include presenters from outside the company.",
                "ans": "B",
                "exp": "Stephan xác nhận tất cả 7 buổi đều diễn ra tại văn phòng midtown (all be held at the midtown office)."
            }
        ]
    },
    {
        "text": "Questions 172–175 refer to the following article.\n\nResearch Findings Presented\n\nGALWAY (1 July)—Eva Urban and her research team at the Ireland Agronomy Association presented their findings to the Galway Department of Transportation on Thursday. During their three-year study, the team was tasked with researching ways to improve the success of tree and shrub plantings along roadways. — [1] —.\n\n\"The ground next to newly paved roads is often compacted by heavy machinery associated with construction,\" Ms. Urban said. \"As a result, the soil can't absorb water or nutrients well, which makes it difficult for new growth to establish itself. — [2] —. My team set up different experimental plots alongside highways and tried various combinations of planting, tilling, and amending soils to determine what worked.\"\n\nThe final results of the government-sponsored research project were compiled into a 50-page handbook. Although the handbook was written specifically for the Galway Department of Transportation, its recommendations can be applied by municipal agencies throughout the country. — [3] —.\n\n\"Each chapter explores one of the ten best practices identified by the team,\" said Ms. Urban. \"These basic techniques are relevant regardless of where they are implemented. The only site-specific variable is plant selection, as that will depend upon the particular geographic region.\"\n\nAnother point conveyed by the study is that successful plant establishment requires an integrated approach. — [4] —. Improving roadside planting requires a thorough assessment of a site's existing conditions as well as a wide variety of management practices to address the specific issues involved.",
        "questions": [
            {
                "num": 172,
                "text": "172. What is the subject of the research discussed in the article?",
                "a": "(A) Keeping vegetation alive along roadways", "b": "(B) Preventing damage to highway surfaces", "c": "(C) Advocating for the use of native plants", "d": "(D) Improving roadside visibility for drivers",
                "ans": "A",
                "exp": "Nghiên cứu tìm giải pháp nâng cao tỷ lệ sống/phát triển của cây trồng ven đường giao thông."
            },
            {
                "num": 173,
                "text": "173. Why does Ms. Urban mention heavy machinery?",
                "a": "(A) To explain why plants may grow poorly in some soil", "b": "(B) To argue that roads can be built more efficiently", "c": "(C) To suggest that road maintenance crews should be careful with young plants", "d": "(D) To describe equipment used by her research team",
                "ans": "A",
                "exp": "Máy móc hạng nặng làm nén đất, khiến đất khó hấp thụ nước/dinh dưỡng làm cây khó phát triển."
            },
            {
                "num": 174,
                "text": "174. In the article, what is indicated about a handbook?",
                "a": "(A) It is only ten pages long.", "b": "(B) It will be distributed to the public.", "c": "(C) It was the subject of a local dispute.", "d": "(D) It is appropriate for use in other parts of the country.",
                "ans": "D",
                "exp": "Bài viết nêu các khuyến nghị trong sổ tay có thể áp dụng cho các cơ quan trên toàn quốc."
            },
            {
                "num": 175,
                "text": "175. In which of the positions marked [1], [2], [3], and [4] does the following sentence best belong?\n\n\"In other words, one action is not enough.\"",
                "a": "(A) [1]", "b": "(B) [2]", "c": "(C) [3]", "d": "(D) [4]",
                "ans": "D",
                "exp": "Vị trí [4] đứng sau câu 'cần một phương pháp tiếp cận toàn diện' -> 'Nói cách khác, một hành động đơn lẻ là không đủ' (In other words, one action is not enough)."
            }
        ]
    },
    {
        "text": "Questions 176–180 refer to the following invoice and article.\n\nINVOICE — Dawn Sky Catering | 525 Horseshoe Lane, Gardendale, PA 19061\nInvoice date: December 6 | Invoice number: 5688\nCustomer: Maureen Shibata | Company: Gardendale Neighborhood Association (GNA)\nAddress: 4069 Strother Street, Gardendale, PA 19061\nPhone: 484-555-0152 | Email: mshibata@gardendalena.org\nEvent date: December 15 | Balance due date: December 13\n\nPlatter of assorted raw vegetables with dips (x5) .......... $125.00\nGrilled chicken skewers - tray (x5) .......... $150.00\nQuiche tarts - tray (x5) .......... $175.00\nSmall chocolate cakes, custom decorated (x50) .......... $250.00\n\nSubtotal: $700.00 | Deposit (received November 25): -$200.00 | BALANCE DUE: $500.00\nComments: See November 30 e-mail from Ms. Shibata about cake design. This will be for the GNA's annual reception.\n\n---\n\nGARDENDALE (December 20)—The Gardendale Neighborhood Association (GNA) honored Mayor Karla Fugate at its annual reception last Saturday. Mayor Fugate had been asked to give a short speech about the city's plans to build a new recreational center, after which she was presented with a special plaque to thank her for her role in the Westside Park project. According to GNA president Manuel Yuen, \"Mayor Fugate was instrumental in making last year's fund-raising festival for the park a huge success.\"\n\nThe festival raised thousands of dollars more than the GNA expected. \"It was a delightful surprise,\" said Mayor Fugate. \"We set ourselves a difficult mission with the park project, but everybody in the GNA and the community at large came through admirably,\" the mayor continued. The GNA reception was held in the Gardendale Botanical Garden, which offered a beautiful setting. The food was provided by Dawn Sky Catering, which included an individual chocolate cake for each guest decorated with the GNA logo.",
        "questions": [
            {
                "num": 176,
                "text": "176. What does the invoice suggest about Ms. Shibata?",
                "a": "(A) She will be the guest of honor at an event.", "b": "(B) She charged the GNA for its catering order.", "c": "(C) She is the organizer of the GNA's reception.", "d": "(D) She will be decorating some cakes herself.",
                "ans": "C",
                "exp": "Trên hóa đơn Ms. Shibata đứng tên khách hàng đặt đồ ăn cho buổi đón tiếp hàng năm của GNA."
            },
            {
                "num": 177,
                "text": "177. When was the GNA required to pay $500 to Dawn Sky Catering?",
                "a": "(A) On November 30", "b": "(B) On December 6", "c": "(C) On December 13", "d": "(D) On December 15",
                "ans": "C",
                "exp": "Hóa đơn ghi 'Balance due date: December 13' cho khoản tiền còn lại $500."
            },
            {
                "num": 178,
                "text": "178. According to the article, what happened at the reception?",
                "a": "(A) Mayor Fugate was given an award.", "b": "(B) Mayor Fugate was asked to reduce her speech.", "c": "(C) Mayor Fugate took questions from the audience.", "d": "(D) Mayor Fugate was invited to join the GNA.",
                "ans": "A",
                "exp": "Bài báo đưa tin Thị trưởng Fugate được trao tặng biểu trưng/bảng vinh danh đặc biệt (presented with a special plaque)."
            },
            {
                "num": 179,
                "text": "179. In the article, the word \"instrumental\" in paragraph 1, line 12, is closest in meaning to",
                "a": "(A) mechanical", "b": "(B) informal", "c": "(C) musical", "d": "(D) essential",
                "ans": "D",
                "exp": "instrumental trong ngữ cảnh này nghĩa là đóng vai trò quan trọng/thiết yếu (essential)."
            },
            {
                "num": 180,
                "text": "180. How many people most likely attended the GNA reception?",
                "a": "(A) 5", "b": "(B) 50", "c": "(C) 100", "d": "(D) 200",
                "ans": "B",
                "exp": "Hóa đơn đặt 50 bánh chocolate nhỏ và bài báo đề cập mỗi khách mời nhận được 1 chiếc bánh logo GNA => Có 50 khách tham dự."
            }
        ]
    },
    {
        "text": "Questions 181–185 refer to the following letter and e-mail.\n\nChisaka Gaming Systems\n410-1109, Nijo Dencho, Nakagyo-ku\nKyoto-shi, Kyoto, Japan\n\nToby Heisenberger | 1226 Lark Street, Albany, New York 12210, USA\nMay 7\nProduct Recall: CGS-P27 High-Speed Gaming Computer\n\nDear Mr. Heisenberger,\nThis is to inform you that the CGS-P27 High-Speed Gaming Computer has been recalled. We have received reports of units overheating and becoming unusable. To address this issue, an additional fan needs to be installed in your computer. Please return the gaming system to the store in which it was purchased, using your personal customer identification number, PCI-70734. Your system will then be sent back to the manufacturer and repaired at no expense to you. We apologize for any inconvenience.\n\nSincerely,\nKobu Matsui, Vice President, Chisaka Gaming Systems\n\n---\n\nTo: Virginia Granger <v.granger@chisakagamingsystems.jp>\nFrom: Jennifer Kinkaid <jkinkaid@albancgm.com>\nDate: June 12\nSubject: Product recall\n\nDear Ms. Granger,\nOur retail stores have been accepting your CGS-P27 High-Speed Gaming Computers for repairs as arranged. As you may know, owners of your gaming system are reluctant to give up their devices for repair once they find that they will be without the system for two to three weeks. Today alone, three customers (PCI-70734, PCI-17503, and PCI-90022) declined to have their systems repaired. The good news is that users of your gaming system are very loyal. However, to increase compliance with the recall and as a public relations gesture, you could provide us with several devices as part of a loaner program. Let me know how I can assist with this arrangement. Thank you!\n\nJennifer Kinkaid, Alban Computers, Games, and More",
        "questions": [
            {
                "num": 181,
                "text": "181. Why did Mr. Matsui send the letter?",
                "a": "(A) To advertise a new product", "b": "(B) To alert a customer to a problem", "c": "(C) To confirm that a refund had been issued", "d": "(D) To offer a customer an upgrade",
                "ans": "B",
                "exp": "Thư gửi thông báo triệu hồi máy tính do sự cố quá nhiệt."
            },
            {
                "num": 182,
                "text": "182. What type of company does Ms. Granger work for?",
                "a": "(A) A computer manufacturer", "b": "(B) A retail store", "c": "(C) A repair company", "d": "(D) A game rental service",
                "ans": "A",
                "exp": "Cô Granger làm việc tại chisakagamingsystems.jp (công ty sản xuất máy tính Chisaka)."
            },
            {
                "num": 183,
                "text": "183. In the e-mail, the word \"program\" in paragraph 2, line 3, is closest in meaning to",
                "a": "(A) schedule", "b": "(B) plan", "c": "(C) broadcast", "d": "(D) software",
                "ans": "B",
                "exp": "loaner program nghĩa là chương trình/kế hoạch cho mượn thiết bị (loaner plan)."
            },
            {
                "num": 184,
                "text": "184. What can be concluded about Mr. Heisenberger?",
                "a": "(A) He was not satisfied with his purchase.", "b": "(B) He called Ms. Granger to discuss options.", "c": "(C) He did not bring his system in for repair.", "d": "(D) He requested a two-week turnaround.",
                "ans": "C",
                "exp": "Trong thư email, mã khách hàng PCI-70734 (ông Heisenberger) nằm trong số những khách hàng từ chối gửi máy lại sửa vì thời gian chờ 2-3 tuần quá lâu."
            },
            {
                "num": 185,
                "text": "185. What does Ms. Kinkaid request in her e-mail?",
                "a": "(A) Free products", "b": "(B) System upgrades", "c": "(C) Computer monitors", "d": "(D) Temporary replacements",
                "ans": "D",
                "exp": "Cô Kinkaid đề xuất gửi một số thiết bị cho mượn tạm thời trong lúc sửa (temporary replacements)."
            }
        ]
    },
    {
        "text": "Questions 186–190 refer to the following e-mail and Web pages.\n\n── E-MAIL ──\nTo: Marcella Wairimu <m.wairimu@theushindigroup.co.ke>\nFrom: Henry Bunyasi <h.bunyasi@theushindigroup.co.ke>\nDate: 3 February\nSubject: Survey\n\nDear Ms. Wairimu,\nThe management team has asked us to find out how satisfied our clients are with our digital marketing services. To that end, we will conduct a survey during the month of April. Given your expertise in survey design and analysis, I would like you to develop a customer satisfaction survey that includes an evaluation of the digital marketing services we advertise on our Web site. It will be sent to each of our longtime clients here in Kenya. Please have a draft ready by 17 February and distribute it to the members of the management team for their review. You and I will present the draft at the management team's meeting on 23 February at 2:00 P.M.\n\nRegards,\nHenry Bunyasi\n\n── WEB PAGE 1: https://www.theushindigroup.co.ke/services_survey ──\nSatisfaction Survey — 1 May\nAt The Ushindi Group, we strive to provide you with top-quality marketing services. That is why we are asking our longtime clients to complete this short survey about our digital marketing services. With the information you provide, we can identify areas for improvement. Please submit your responses on or before 19 May. Thank you for helping us to serve you better.\n\nPlease type one of the following values into the appropriate box for each service.\n1 = very dissatisfied, 2 = dissatisfied, 3 = no opinion, 4 = satisfied, 5 = very satisfied\nDigital Marketing Services:\nA. Advertising on social media [ ]\nB. Content creation, including written content, photos, and videos [ ]\nC. E-mail marketing to existing and potential customers [ ]\nD. Web and mobile app development and design [ ]\nClient name (optional): _______________\n\n── WEB PAGE 2: https://www.theushindigroup.co.ke/companynews ──\nImprovements to Our Services\nIn response to customer feedback, The Ushindi Group will introduce a new e-mail marketing strategy on 15 July. Our new focus will be on triggered e-mails. Triggered e-mails are sent out automatically based on customer behaviour and have a much higher response rate than traditional marketing e-mails. Triggered e-mails help companies turn casual buyers into loyal customers. We anticipate that this change will result in a noticeable increase in repeat customers for our clients. The price of our services will remain the same. For more information, you may contact your marketing account manager directly, call The Ushindi Group at 0800 205 555, or send an e-mail to info@theushindigroup.co.ke.",
        "questions": [
            {
                "num": 186,
                "text": "186. What is stated about Ms. Wairimu in the e-mail?",
                "a": "(A) She resolved a complaint from one of her clients.", "b": "(B) She responded to an employee questionnaire.", "c": "(C) She is a member of the management team.", "d": "(D) She is highly skilled in survey development.",
                "ans": "D",
                "exp": "Email có viết: 'Given your expertise in survey design and analysis...' => Cô ấy rất giỏi thiết kế khảo sát."
            },
            {
                "num": 187,
                "text": "187. What will most likely happen on February 23?",
                "a": "(A) The Ushindi Group's Web site will be updated.", "b": "(B) Mr. Bunyasi will review the advertising budget.", "c": "(C) Ms. Wairimu will attend a meeting in the afternoon.", "d": "(D) The management team will vote on a policy revision.",
                "ans": "C",
                "exp": "Bunyasi đề nghị cùng Ms. Wairimu thuyết trình dự thảo khảo sát tại buổi họp ban quản lý lúc 2 giờ chiều ngày 23/2."
            },
            {
                "num": 188,
                "text": "188. What can be concluded about the satisfaction survey?",
                "a": "(A) It was sent by mail.", "b": "(B) It was not distributed to clients according to the original timetable.", "c": "(C) It was revised after the management team's meeting.", "d": "(D) It was sent to clients around the world.",
                "ans": "B",
                "exp": "Email định dạng khảo sát diễn ra trong tháng 4, nhưng trang web khảo sát ghi ngày mở là 1/5 => Bị trễ so với kế hoạch ban đầu."
            },
            {
                "num": 189,
                "text": "189. What news is reported on the second Web page?",
                "a": "(A) Service rates will soon increase.", "b": "(B) A marketing manager has been replaced.", "c": "(C) Surveys will be conducted on a monthly basis.", "d": "(D) An automated customer contact system will launch.",
                "ans": "D",
                "exp": "The Ushindi Group ra mắt hệ thống e-mail marketing tự động (triggered e-mails) dựa trên hành vi khách hàng."
            },
            {
                "num": 190,
                "text": "190. What digital marketing service will The Ushindi Group change based on responses to its survey?",
                "a": "(A) Service A", "b": "(B) Service B", "c": "(C) Service C", "d": "(D) Service D",
                "ans": "C",
                "exp": "Trang tin tức đề cập cải tiến dịch vụ 'e-mail marketing', đây chính là dịch vụ C trong bảng khảo sát."
            }
        ]
    },
    {
        "text": "Questions 191–195 refer to the following article and Web pages.\n\n── ARTICLE ──\nDirector Rubio Celebrated\nMERRINGTON (July 20)—Although Pedro Rubio retired from directing ten years ago, his award-winning films still influence today's cinema. Rubio's childhood home was near a movie house, where he fell in love with the art form. He saw several movies a week, sometimes watching the same movie multiple times. His extensive familiarity with a range of genres is apparent in his work. Titles range from the romantic Send Me Some Roses to the horror classic That House. Rubio retired from filmmaking at age 65 after almost 40 years of directing, but he has kept busy. Most recently, he has been working as a guest lecturer at the nearby Weberton Film School. Readers will be pleased to hear that our own Merrington Cinema will be showing Rubio's films throughout August. Whether you are a longtime fan or have never seen a Rubio film, you will surely enjoy this offering at Merrington Cinema.\n\n── WEB PAGE 1: https://www.merringtoncinema.com ──\nChoose Your Own Double Feature\nIn August, we will celebrate the acclaimed director Pedro Rubio's birthday by showing many of his movies. And you can purchase tickets to two movies for the price of one! Rubio made the films listed below at the beginning of his directing career. See the Schedule page for the complete list of films and their weekly viewing times.\n\nPut a Roof on It, Comedy, 102 minutes\nConstruction workers do their best to build a wealthy man's dream home while his brother tries to take over the project.\n\nThrough a Diamond Rain, Science Fiction, 124 minutes\nTwo teams of researchers travel to Neptune and try to send their findings back to Earth.\n\nWeekends and Memories, Drama, 115 minutes\nA group of old friends gather at a country house and discover that much has changed since they were last together. This film won the Gold Dreamer Award.\n\nThe Strange Drive, Western, 107 minutes\nCowboys on a cattle drive encounter a series of interesting and unusual strangers.\n\n── WEB PAGE 2: https://www.merringtoncinema.com/reviews ──\nI recently read a great article about director Pedro Rubio. It contained a lot of information about his work and life, including some surprising information about what he has been doing since he retired from filmmaking. The article also mentioned that Merrington Cinema would be showing his films. So I went to the cinema's Web site and saw the two-for-one deal. I thought this would be an excellent way to spend a Saturday, so I went! I saw two wonderful movies. One of the films I saw was new to me: it was about scientists on a mission in space. I loved it! For a movie fan like me, Merrington Cinema's promotion was perfect. I understand there will be a similar promotion for Meredeth Bui's films in October. I'll be sure to take advantage of great offers like this again.\n—Talia Pak",
        "questions": [
            {
                "num": 191,
                "text": "191. According to the article, how did Mr. Rubio become interested in the cinema?",
                "a": "(A) His family worked in the movie business.", "b": "(B) He participated in a film club at school.", "c": "(C) He visited a movie theater frequently in his youth.", "d": "(D) He used to be a ticket seller in a movie theater.",
                "ans": "C",
                "exp": "Bài báo nêu: 'Rubio's childhood home was near a movie house, where he fell in love with the art form. He saw several movies a week...'"
            },
            {
                "num": 192,
                "text": "192. According to the first Web page, why is Merrington Cinema offering a promotion?",
                "a": "(A) It recently opened and wants to attract customers.", "b": "(B) It is celebrating a director's birthday.", "c": "(C) It has partnered with a movie studio to show certain movies.", "d": "(D) It wants to advertise its new upgraded premises.",
                "ans": "B",
                "exp": "Trang web 1 ghi: 'In August, we will celebrate the acclaimed director Pedro Rubio's birthday by...'"
            },
            {
                "num": 193,
                "text": "193. According to the first Web page, what do the four listed movies have in common?",
                "a": "(A) They are all less than 120 minutes long.", "b": "(B) They all focus on friendships.", "c": "(C) They are all early films of Mr. Rubio's.", "d": "(D) They have all received awards.",
                "ans": "C",
                "exp": "Trang web 1 ghi: 'Rubio made the films listed below at the beginning of his directing career.'"
            },
            {
                "num": 194,
                "text": "194. What did Ms. Pak find surprising about Mr. Rubio?",
                "a": "(A) He is teaching at a local film school.", "b": "(B) He directed movies for nearly 40 years.", "c": "(C) He worked in many genres.", "d": "(D) He has opened his own movie theater.",
                "ans": "A",
                "exp": "Bài báo nói Rubio giảng dạy tại Weberton Film School sau khi nghỉ hưu. Talia Pak viết bài báo chứa thông tin gây bất ngờ về hoạt động của Rubio sau khi nghỉ hưu."
            },
            {
                "num": 195,
                "text": "195. What movie did Ms. Pak see recently for the first time?",
                "a": "(A) Put a Roof on It", "b": "(B) Through a Diamond Rain", "c": "(C) Weekends and Memories", "d": "(D) The Strange Drive",
                "ans": "B",
                "exp": "Cô nói bộ phim mới xem kể về các nhà khoa học trong không gian => Đó là bộ phim khoa học viễn tưởng 'Through a Diamond Rain'."
            }
        ]
    },
    {
        "text": "Questions 196–200 refer to the following policy and e-mails.\n\n── SUBMISSION POLICY ──\nUndeniable is an ad-supported literary journal of short fiction and nonfiction by emerging writers. We waive our $5 fee for first-time submitters.\n• Stories must be between 250 and 1,000 words (no poetry, please).\n• Do not include illustrations. All illustrations are produced in-house.\n• Attach your story in an e-mail to: submissions@undeniable.com. Please include a brief synopsis of your piece, and tell us how you discovered Undeniable.\n• We pay a $50 honorarium upon acceptance for publication.\n• If we accept your story, we will send you a contract and a form to set up an electronic money transfer.\n\n── E-MAIL 1 ──\nTo: submissions@undeniable.com\nFrom: len.sutherland@onyxmail.com\nDate: March 15\nSubject: Cover letter and submission\nAttachment: Ji's Journey\n\nGreetings!\nMy submission, \"Ji's Journey,\" centers on a young dress designer, Toby Ji, who overcomes obstacles to realize her dreams in the fashion industry. I was introduced to Undeniable last year by my writing instructor at the Artman Institute in Portland, Oregon, and have since become a subscriber. I particularly enjoy your Nonfiction Corner; one of my favorites was \"Waygone Beach,\" which inspired me to write \"Ji's Journey.\" I believe it would be an ideal fit for this section. Like \"Waygone Beach,\" \"Ji's Journey\" is a true story of hope and perseverance. Thank you for your consideration and for creating a forum for new writers like me.\n\nSincerely,\nLen Sutherland\n\n── E-MAIL 2 ──\nTo: len.sutherland@onyxmail.com\nFrom: jerrybuckman@undeniable.com\nDate: July 2\nSubject: Your submission\n\nDear Mr. Sutherland,\nYour story, \"Ji's Journey,\" generated a great deal of positive feedback about the June issue. Congratulations! And your instincts were correct regarding your story's placement. All this has us hoping you will submit more stories to Undeniable. As an added incentive, we will be increasing our honorarium to $100 beginning next month.\n\nAs a subscriber, you are likely familiar with Stacy Jordan's question-and-answer column featuring a different writer each month. Would you be willing to answer a few questions about your literary training, writing method, and how you find story ideas? If so, I will forward your e-mail address to Ms. Jordan, who will reach out to you in the near future.\n\nSincerely,\nJerry Buckman\nAssociate Editor",
        "questions": [
            {
                "num": 196,
                "text": "196. What does the policy indicate about Undeniable?",
                "a": "(A) It does not accept poems.", "b": "(B) It has no advertisements.", "c": "(C) It requires writers to submit drawings.", "d": "(D) It publishes the work of famous authors.",
                "ans": "A",
                "exp": "Dòng đầu tiên của quy định: 'no poetry, please' (không nhận thơ)."
            },
            {
                "num": 197,
                "text": "197. According to the first e-mail, where did Mr. Sutherland discover Undeniable?",
                "a": "(A) In a public library", "b": "(B) In a school bookstore", "c": "(C) In a writing class", "d": "(D) In a clothing shop",
                "ans": "C",
                "exp": "Sutherland được giới thiệu bởi giảng viên dạy viết của mình ('my writing instructor') tại Artman Institute."
            },
            {
                "num": 198,
                "text": "198. What can be concluded about \"Waygone Beach\"?",
                "a": "(A) It takes place in Portland, Oregon.", "b": "(B) It was not accepted for publication.", "c": "(C) It is Mr. Sutherland's first story.", "d": "(D) It does not exceed 1,000 words.",
                "ans": "D",
                "exp": "Mọi tác phẩm đăng trên tập san phải tuân thủ chính sách: độ dài từ 250 đến 1,000 từ. Do đó, 'Waygone Beach' (đã xuất bản) không thể quá 1,000 từ."
            },
            {
                "num": 199,
                "text": "199. How much did Mr. Sutherland receive for his story in the June issue of Undeniable?",
                "a": "(A) $5", "b": "(B) $50", "c": "(C) $100", "d": "(D) $250",
                "ans": "B",
                "exp": "Chính sách ban đầu trả $50 tiền thù lao ('$50 honorarium'). Kế hoạch tăng thù lao lên $100 chỉ bắt đầu vào tháng sau (tháng 8)."
            },
            {
                "num": 200,
                "text": "200. What does the second e-mail suggest about Ms. Jordan?",
                "a": "(A) She plans to renew her subscription.", "b": "(B) She writes a column for Undeniable.", "c": "(C) She teaches writing classes.", "d": "(D) She has an unusual writing method.",
                "ans": "B",
                "exp": "Jerry Buckman viết: 'Stacy Jordan's question-and-answer column...' => Stacy Jordan phụ trách một chuyên mục chuyên phỏng vấn tác giả mỗi tháng trên tập san."
            }
        ]
    }
]

def seed_toeic():
    app = create_app()
    with app.app_context():
        db.create_all()
        # Check if the test is already seeded
        test = ToeicTest.query.filter_by(title="Đề thi thử TOEIC Reading số 1").first()
        if not test:
            test = ToeicTest(title="Đề thi thử TOEIC Reading số 1")
            db.session.add(test)
            db.session.flush()
            print(f"Created ToeicTest ID: {test.id}")
        else:
            # Clean existing to re-seed cleanly
            ToeicQuestion.query.filter_by(test_id=test.id).delete()
            ToeicPassage.query.filter_by(test_id=test.id).delete()
            db.session.commit()
            print(f"Cleared existing questions/passages for test ID: {test.id}")

        # Seed Part 5 questions
        for q in PART_5_QUESTIONS:
            question = ToeicQuestion(
                test_id=test.id,
                passage_id=None,
                part=5,
                question_number=q["num"],
                question_text=q["text"],
                option_a=q["a"],
                option_b=q["b"],
                option_c=q["c"],
                option_d=q["d"],
                correct_option=q["ans"],
                explanation=q["exp"]
            )
            db.session.add(question)

        # Seed Part 6 passages and questions
        for p in PART_6_PASSAGES:
            passage = ToeicPassage(
                test_id=test.id,
                part=6,
                passage_text=p["text"]
            )
            db.session.add(passage)
            db.session.flush()

            for q in p["questions"]:
                question = ToeicQuestion(
                    test_id=test.id,
                    passage_id=passage.id,
                    part=6,
                    question_number=q["num"],
                    question_text=q["text"],
                    option_a=q["a"],
                    option_b=q["b"],
                    option_c=q["c"],
                    option_d=q["d"],
                    correct_option=q["ans"],
                    explanation=q["exp"]
                )
                db.session.add(question)

        # Seed Part 7 passages and questions
        for p in PART_7_PASSAGES:
            passage = ToeicPassage(
                test_id=test.id,
                part=7,
                passage_text=p["text"]
            )
            db.session.add(passage)
            db.session.flush()

            for q in p["questions"]:
                question = ToeicQuestion(
                    test_id=test.id,
                    passage_id=passage.id,
                    part=7,
                    question_number=q["num"],
                    question_text=q["text"],
                    option_a=q["a"],
                    option_b=q["b"],
                    option_c=q["c"],
                    option_d=q["d"],
                    correct_option=q["ans"],
                    explanation=q["exp"]
                )
                db.session.add(question)

        db.session.commit()
        print("TOEIC test seeded successfully!")
        print(f"Total TOEIC Questions: {ToeicQuestion.query.filter_by(test_id=test.id).count()}")

if __name__ == "__main__":
    seed_toeic()
